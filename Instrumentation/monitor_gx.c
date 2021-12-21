#define _CRT_SECURE_NO_WARNINGS

#define MAP_SIZE 65536
#define BUF_SIZE 65537 // buf[0] is flag, buf[1-65536] map,

#include "dr_api.h"
#include "drmgr.h"
#include "drx.h"
#include "drreg.h"
#include "drwrap.h"
#include "hash.h"

#ifdef USE_DRSYMS
#include "drsyms.h"
#endif

#include "modules.h"
#include "utils.h"
#include "hashtable.h"
#include "drtable.h"
#include "limits.h"
#include <string.h>
#define WIN32_LEAN_AND_MEAN
#include <stdlib.h>
#include <windows.h>
#include <stdio.h>
#include <tchar.h>
#include <winsock2.h>
#include <ws2tcpip.h>

#define UNKNOWN_MODULE_ID USHRT_MAX

#ifndef PF_FASTFAIL_AVAILABLE
#define PF_FASTFAIL_AVAILABLE 23
#endif

#ifndef STATUS_FATAL_APP_EXIT
#define STATUS_FATAL_APP_EXIT ((DWORD)0x40000015L)
#endif

#ifndef STATUS_HEAP_CORRUPTION
#define STATUS_HEAP_CORRUPTION 0xC0000374
#endif

static uint verbose;

#define NOTIFY(level, fmt, ...) do {          \
    if (verbose >= (level))                   \
        dr_fprintf(STDERR, fmt, __VA_ARGS__); \
} while (0)

#define OPTION_MAX_LENGTH MAXIMUM_PATH

#define COVERAGE_BB 0
#define COVERAGE_EDGE 1

//fuzz modes
enum persistence_mode_t { native_mode = 0,	in_app = 1,};

typedef struct _target_module_t {
    char module_name[MAXIMUM_PATH];
    struct _target_module_t *next;
} target_module_t;


#define NUM_THREAD_MODULE_CACHE 4

typedef struct _winafl_data_t {
    module_entry_t *cache[NUM_THREAD_MODULE_CACHE];
    file_t  log;
    unsigned char *fake_afl_area; //used for thread_coverage
    unsigned char *afl_area;
} winafl_data_t;
static winafl_data_t winafl_data;

static int thread_tls_field;
static int tls_ctl_field;

typedef struct _fuzz_target_t {
    reg_t xsp;            /* stack level at entry to the fuzz target */
    app_pc func_pc;
    int iteration;
} fuzz_target_t;

static fuzz_target_t fuzz_target;

typedef struct _debug_data_t {
    int pre_hanlder_called;
    int post_handler_called;
} debug_data_t;

/* Thread-private data */
typedef struct {
    bool dump_flag;
    bool start_flag;
    
} thread_ctl_t; // control start of recording and end of recording

static debug_data_t debug_data;

static int libmap[MAP_SIZE]; 

static module_table_t *module_table;
static client_id_t client_id;

static volatile bool go_native;
unsigned char *thread_afl_area;
static unsigned char recv_index; 
static int crash_tag = 0;
void *as_built_lock;


static int write_to_shm(unsigned char *buf,int size){
    HANDLE hMapFile = OpenFileMapping(
        FILE_MAP_ALL_ACCESS,
        FALSE,
        L"sharedMemory"
        );
    // HANDLE hMapFile = CreateFileMapping(
    //     INVALID_HANDLE_VALUE,
    //     NULL,
    //     PAGE_READWRITE,
    //     0,
    //     BUF_SIZE,
    //     L"sharedMemory"
    //     ); 

    if (hMapFile){
        LPVOID lpBase = MapViewOfFile(
            hMapFile, 
            FILE_MAP_ALL_ACCESS,
            0,
            0,
            BUF_SIZE
            );

        unsigned char *ptr = (char *)lpBase;
        ptr[0] = recv_index;
        for (int i=0;i<BUF_SIZE;i++)
        {
            if (ptr[i]==0 && buf[i]!=0){
                ptr[i] = buf[i];
            }
        }
        // memcpy(&ptr[1],buf,size);
        if (crash_tag==1){
            ptr[BUF_SIZE-1] = 0xff; // represent there is a crash
        }
        
        UnmapViewOfFile(lpBase);
        CloseHandle(hMapFile);

        return 0;
    }else{
        return -1;
    }

    return 0;
}

static void
event_exit(void);

static void
event_thread_exit(void *drcontext);

static HANDLE pipe;

/****************************************************************************
 * Nudges
 */

enum {
    NUDGE_TERMINATE_PROCESS = 1,
};

static void
event_nudge(void *drcontext, uint64 argument)
{
    int nudge_arg = (int)argument;
    int exit_arg  = (int)(argument >> 32);
    if (nudge_arg == NUDGE_TERMINATE_PROCESS) {
        static int nudge_term_count;
        /* handle multiple from both NtTerminateProcess and NtTerminateJobObject */
        uint count = dr_atomic_add32_return_sum(&nudge_term_count, 1);
        if (count == 1) {
            dr_exit_process(exit_arg);
        }
    }
    ASSERT(nudge_arg == NUDGE_TERMINATE_PROCESS, "unsupported nudge");
    ASSERT(false, "should not reach"); /* should not reach */
}

static bool
event_soft_kill(process_id_t pid, int exit_code)
{
    /* we pass [exit_code, NUDGE_TERMINATE_PROCESS] to target process */
    dr_config_status_t res;
    res = dr_nudge_client_ex(pid, client_id,
                             NUDGE_TERMINATE_PROCESS | (uint64)exit_code << 32,
                             0);
    if (res == DR_SUCCESS) {
        /* skip syscall since target will terminate itself */
        return true;
    }
    /* else failed b/c target not under DR control or maybe some other
     * error: let syscall go through
     */
    return false;
}


static bool onexception(void *drcontext, dr_exception_t *excpt) {
    DWORD exception_code = excpt->record->ExceptionCode;
    
   
    if((exception_code == EXCEPTION_ACCESS_VIOLATION) ||
       (exception_code == EXCEPTION_ILLEGAL_INSTRUCTION) ||
       (exception_code == EXCEPTION_PRIV_INSTRUCTION) ||
       (exception_code == EXCEPTION_INT_DIVIDE_BY_ZERO) ||
       (exception_code == STATUS_HEAP_CORRUPTION) ||
       (exception_code == EXCEPTION_STACK_OVERFLOW) ||
       (exception_code == STATUS_STACK_BUFFER_OVERRUN) ||
       (exception_code == STATUS_FATAL_APP_EXIT)) {
        
        thread_ctl_t *tls_ctl_data;
        tls_ctl_data = drmgr_get_tls_field(drcontext, tls_ctl_field);

        void **thread_data = (void **)drmgr_get_tls_field(drcontext, thread_tls_field);
        unsigned char *map = thread_data[1];

        // u32 cksum = hash32((u8 *)map, MAP_SIZE, HASH_CONST); // dump map to log file
        crash_tag = 1;
        write_to_shm(map,MAP_SIZE);    
        char errorMessage[50];
        memset(errorMessage,0,50);

        // snprintf(errorMessage, 50 ,"Exception caught:%x\n",exception_code);
        // DR_ASSERT_MSG(false, errorMessage);
        dr_exit_process(1);
    
    }
    
    return true;
}

static void event_thread_init(void *drcontext)
{
  void **thread_data;

  thread_data = (void **)dr_thread_alloc(drcontext, 2 * sizeof(void *));
  unsigned char * thread_afl_area =  (unsigned char *)dr_global_alloc(MAP_SIZE);
  thread_data[0] = 0;
  
  thread_data[1] = thread_afl_area; // by fdl
  memset(thread_afl_area,0,MAP_SIZE); // clear the memory before operation

  drmgr_set_tls_field(drcontext, thread_tls_field, thread_data); 

  thread_ctl_t* tls_ctl_data;
  tls_ctl_data = (thread_ctl_t *) dr_thread_alloc(drcontext, sizeof(thread_ctl_t));
  drmgr_set_tls_field(drcontext, tls_ctl_field, tls_ctl_data);
  
  tls_ctl_data->start_flag = false;
  tls_ctl_data->dump_flag = true;

}

static void event_thread_exit(void *drcontext)
{
  void **data = drmgr_get_tls_field(drcontext, thread_tls_field);
  dr_thread_free(drcontext,data[1],MAP_SIZE);
  dr_thread_free(drcontext, data, 2 * sizeof(void *));

  thread_ctl_t *tls_ctl_data;
  tls_ctl_data = drmgr_get_tls_field(drcontext, tls_ctl_field);
  
  dr_thread_free(drcontext, tls_ctl_data, sizeof(thread_ctl_t));

}

static dr_emit_flags_t instrument_bb_coverage(void *drcontext, void *tag, instrlist_t *bb, instr_t *inst,
                      bool for_trace, bool translating, void *user_data)
{
    static bool debug_information_output = false;
    app_pc start_pc;
    module_entry_t **mod_entry_cache;
    module_entry_t *mod_entry;
    const char *module_name;
    uint offset;
    target_module_t *target_modules;
    bool should_instrument;
    unsigned char *afl_map;
	dr_emit_flags_t ret;

    if (!drmgr_is_first_instr(drcontext, inst))
        return DR_EMIT_DEFAULT;

    should_instrument = false;

    app_pc instr_addr = instr_get_app_pc(inst);

    int base_addr,offset_addr;

    base_addr = ((int)instr_addr & 0xffff0000) >> 16;

    if (libmap[base_addr] == 1)
    {
        should_instrument = true;
    }

    if(!should_instrument) return DR_EMIT_DEFAULT | DR_EMIT_PERSISTABLE;

    offset = (int)instr_addr & 0xffff;
    
    drreg_reserve_aflags(drcontext, bb, inst);

   { 
    reg_id_t reg;
    opnd_t opnd1, opnd2;
    instr_t *new_instr;

    drreg_reserve_register(drcontext, bb, inst, NULL, &reg);

    drmgr_insert_read_tls_field(drcontext, thread_tls_field, bb, inst, reg); // thread_data

    opnd1 = opnd_create_reg(reg); // thread_data[0]
    opnd2 = OPND_CREATE_MEMPTR(reg, sizeof(void *)); // thread_data[1]
    new_instr = INSTR_CREATE_mov_ld(drcontext, opnd1, opnd2);
    instrlist_meta_preinsert(bb, inst, new_instr);

    opnd1 = OPND_CREATE_MEM8(reg, offset);
    new_instr = INSTR_CREATE_inc(drcontext, opnd1);
    instrlist_meta_preinsert(bb, inst, new_instr);

    drreg_unreserve_register(drcontext, bb, inst, reg);

    ret = DR_EMIT_DEFAULT | DR_EMIT_PERSISTABLE;

    drreg_unreserve_aflags(drcontext, bb, inst);
    }

    return ret;
}

static dr_emit_flags_t instrument_edge_coverage(void *drcontext, void *tag, instrlist_t *bb, instr_t *inst,
                      bool for_trace, bool translating, void *user_data)
{
    static bool debug_information_output = false;
    app_pc start_pc;
    module_entry_t **mod_entry_cache;
    module_entry_t *mod_entry;
    reg_id_t reg, reg2, reg3;
    opnd_t opnd1, opnd2;
    instr_t *new_instr;
    const char *module_name;
    uint offset;
    target_module_t *target_modules;
    bool should_instrument;
    dr_emit_flags_t ret;

    if (!drmgr_is_first_instr(drcontext, inst))
        return DR_EMIT_DEFAULT;

    start_pc = dr_fragment_app_pc(tag);

    should_instrument = false;

    app_pc instr_addr = instr_get_app_pc(inst);

    int base_addr,offset_addr;

    base_addr = ((int)instr_addr & 0xffff0000) >> 16;

    if (libmap[base_addr] == 1)
    {
        should_instrument = true;
    }

   

    if(!should_instrument) return DR_EMIT_DEFAULT | DR_EMIT_PERSISTABLE;

    // offset = (uint)(start_pc - mod_entry->data->start);
    offset = (int)instr_addr & 0xffff;
    offset &= MAP_SIZE - 1;

    drreg_reserve_aflags(drcontext, bb, inst);
    drreg_reserve_register(drcontext, bb, inst, NULL, &reg);
    drreg_reserve_register(drcontext, bb, inst, NULL, &reg2);
    drreg_reserve_register(drcontext, bb, inst, NULL, &reg3);

    //reg2 stores AFL area, reg 3 stores previous offset

    //load the pointer to previous offset in reg3
    drmgr_insert_read_tls_field(drcontext, thread_tls_field, bb, inst, reg3);

    //load address of shm into reg2
    // if(options.thread_coverage || options.dr_persist_cache) {
      opnd1 = opnd_create_reg(reg2);
      opnd2 = OPND_CREATE_MEMPTR(reg3, sizeof(void *));
      new_instr = INSTR_CREATE_mov_ld(drcontext, opnd1, opnd2);
      instrlist_meta_preinsert(bb, inst, new_instr);

      ret = DR_EMIT_DEFAULT | DR_EMIT_PERSISTABLE;

    // } else {
    //   opnd1 = opnd_create_reg(reg2);
    //   opnd2 = OPND_CREATE_INTPTR((uint64)winafl_data.afl_area);
    //   new_instr = INSTR_CREATE_mov_imm(drcontext, opnd1, opnd2);
    //   instrlist_meta_preinsert(bb, inst, new_instr);

    //   ret = DR_EMIT_DEFAULT;
    // }

    //load previous offset into register
    opnd1 = opnd_create_reg(reg);
    opnd2 = OPND_CREATE_MEMPTR(reg3, 0);
    new_instr = INSTR_CREATE_mov_ld(drcontext, opnd1, opnd2);
    instrlist_meta_preinsert(bb, inst, new_instr);

    //xor register with the new offset
    opnd1 = opnd_create_reg(reg);
    opnd2 = OPND_CREATE_INT32(offset);
    new_instr = INSTR_CREATE_xor(drcontext, opnd1, opnd2);
    instrlist_meta_preinsert(bb, inst, new_instr);

    //increase the counter at reg + reg2
    opnd1 = opnd_create_base_disp(reg2, reg, 1, 0, OPSZ_1);
    new_instr = INSTR_CREATE_inc(drcontext, opnd1);
    instrlist_meta_preinsert(bb, inst, new_instr);

    //store the new value
    offset = (offset >> 1)&(MAP_SIZE - 1);
    opnd1 = OPND_CREATE_MEMPTR(reg3, 0);
    opnd2 = OPND_CREATE_INT32(offset);
    new_instr = INSTR_CREATE_mov_st(drcontext, opnd1, opnd2);
    instrlist_meta_preinsert(bb, inst, new_instr);

    drreg_unreserve_register(drcontext, bb, inst, reg3);
    drreg_unreserve_register(drcontext, bb, inst, reg2);
    drreg_unreserve_register(drcontext, bb, inst, reg);
    drreg_unreserve_aflags(drcontext, bb, inst);

    return ret;
}

static void closesocket_post(void *wrapcxt, void *user_data)
{
    void *drcontext = dr_get_current_drcontext();
    thread_ctl_t *ctl_data = drmgr_get_tls_field(drcontext,tls_ctl_field);
    if (ctl_data->start_flag){
        ctl_data->start_flag = false;
        void **thread_data = (void **)drmgr_get_tls_field(drcontext, thread_tls_field);
        unsigned char *map = thread_data[1];
        write_to_shm(map,MAP_SIZE);
        ctl_data->dump_flag = true; // has dumped to shm
    }
    
}



static void recv_pre(void *wrapcxt, void **user_data){
    // void *drcontext = dr_get_current_drcontext();
    // thread_ctl_t *ctl_data = drmgr_get_tls_field(drcontext,tls_ctl_field);
    
    DWORD buf = (DWORD)drwrap_get_arg(wrapcxt,1);
    *user_data = (void *)buf;
}

static void recv_post(void *wrapcxt, void *user_data)
{
    char* buf = (char *) user_data;
    void *drcontext = dr_get_current_drcontext();
    

    thread_ctl_t *ctl_data = drmgr_get_tls_field(drcontext,tls_ctl_field);

    ctl_data->start_flag = true;

    void **thread_data = (void **)drmgr_get_tls_field(drcontext, thread_tls_field);
    unsigned char *map = thread_data[1];
    dr_mutex_lock(as_built_lock);
    recv_index = recv_index + 1;
    dr_mutex_unlock(as_built_lock);

    if (ctl_data->dump_flag) // start to record a new map 
        {
            memset(map,0,MAP_SIZE); // otherwise it will record the execution of GUI
            ctl_data->dump_flag = false;

        }
}

static void send_post(void *wrapcxt, void *user_data)
{
    void *drcontext = dr_get_current_drcontext();
    thread_ctl_t *ctl_data = drmgr_get_tls_field(drcontext,tls_ctl_field);
    if(ctl_data->start_flag){ // preserve afl_map info, and then do not record
        ctl_data->start_flag = false;
        void **thread_data = (void **)drmgr_get_tls_field(drcontext, thread_tls_field);
        unsigned char *map = thread_data[1];
        write_to_shm(map,MAP_SIZE);
        ctl_data->dump_flag = true;
        
    }

}


static void createfilew_interceptor(void *wrapcxt, INOUT void **user_data)
{
    wchar_t *filenamew = (wchar_t *)drwrap_get_arg(wrapcxt, 0);
    
}

static void createfilea_interceptor(void *wrapcxt, INOUT void **user_data)
{
    char *filename = (char *)drwrap_get_arg(wrapcxt, 0);
    
}

static void verfierstopmessage_interceptor_pre(void *wrapctx, INOUT void **user_data)
{
    EXCEPTION_RECORD exception_record = { 0 };
    dr_exception_t dr_exception = { 0 };
    dr_exception.record = &exception_record;
    exception_record.ExceptionCode = STATUS_HEAP_CORRUPTION;

    onexception(NULL, &dr_exception);
}



static void isprocessorfeaturepresent_interceptor_pre(void *wrapcxt, INOUT void **user_data)
{
    DWORD feature = (DWORD)drwrap_get_arg(wrapcxt, 0);
    *user_data = (void*)feature;
}

static void isprocessorfeaturepresent_interceptor_post(void *wrapcxt, void *user_data)
{
    DWORD feature = (DWORD)user_data;
    if(feature == PF_FASTFAIL_AVAILABLE) { 
        // Make the software thinks that _fastfail() is not supported.
        drwrap_set_retval(wrapcxt, (void*)0);
    }
}

static void unhandledexceptionfilter_interceptor_pre(void *wrapcxt, INOUT void **user_data)
{
    PEXCEPTION_POINTERS exception = (PEXCEPTION_POINTERS)drwrap_get_arg(wrapcxt, 0);
    dr_exception_t dr_exception = { 0 };

    // Fake an exception
    dr_exception.record = exception->ExceptionRecord;
    onexception(NULL, &dr_exception);
}

static void event_module_unload(void *drcontext, const module_data_t *info)
{
    module_table_unload(module_table, info);
}

static void event_module_load(void *drcontext, const module_data_t *info, bool loaded)
{
    const char *module_name = info->names.exe_name;
    const char *full_path = info->full_path;
    int base_addr = ((int)info->start & 0xffff0000 ) >> 16;

    app_pc to_wrap = 0;

    if (module_name == NULL) {
        // In case exe_name is not defined, we will fall back on the preferred name.
        module_name = dr_module_preferred_name(info);
    }

    // if (strstr(full_path, "C:\\WINDOWS")==NULL && strstr(full_path, "C:\\Windows")==NULL
    //      && strstr(full_path, "DynamoRIO") == NULL
    //      && strstr(full_path, "dyna") == NULL
    //      && strstr(full_path, "monitor") == NULL
    //     )
    // if (strstr(full_path, "DynamoRIO") == NULL
    //      && strstr(full_path, "dyna") == NULL
    //      && strstr(full_path, "monitor") == NULL
    //     && strstr(full_path, "MFC71") == NULL)
    // {
    //     libmap[base_addr] = 1; // tag for instrumentation

    // }

    libmap[base_addr] = 1;
    
    
   // if (_stricmp(module_name, "WS2_32.dll") == 0)
   // {
   //     to_wrap = (app_pc)dr_get_proc_address(info->handle, "closesocket");
   //     drwrap_wrap(to_wrap, NULL, closesocket_post);
   //     to_wrap = (app_pc)dr_get_proc_address(info->handle, "recv");
   //     drwrap_wrap(to_wrap, NULL, recv_post);
   //     to_wrap = (app_pc)dr_get_proc_address(info->handle, "send");
   //     drwrap_wrap(to_wrap,NULL, send_post);
   //     to_wrap = (app_pc)dr_get_proc_address(info->handle, "shutdown");
   //     drwrap_wrap(to_wrap,NULL,closesocket_post);
   // }

   if (_stricmp(module_name, "WSOCK32.dll") == 0)
   {
       to_wrap = (app_pc)dr_get_proc_address(info->handle, "closesocket");
       drwrap_wrap(to_wrap, NULL, closesocket_post);
       to_wrap = (app_pc)dr_get_proc_address(info->handle, "recv");
       drwrap_wrap(to_wrap,recv_pre, recv_post);
       to_wrap = (app_pc)dr_get_proc_address(info->handle, "send");
       drwrap_wrap(to_wrap,NULL, send_post);
   }
   



    module_table_load(module_table, info);
}

static void event_exit(void)
{
    
    /* destroy module table */
    module_table_destroy(module_table);
    drx_exit();
    drmgr_exit();
    dr_mutex_destroy(as_built_lock);
}

static void event_init(void)
{   
    module_table = module_table_create();
}


DR_EXPORT void dr_client_main(client_id_t id, int argc, const char *argv[])
{
    drreg_options_t ops = {sizeof(ops), 2 /*max slots needed: aflags*/, false};

    dr_set_client_name("Monitor", "");
    recv_index = 0;

    drmgr_init();
    drx_init();
    drreg_init(&ops);
    drwrap_init();
    as_built_lock = dr_mutex_create();

    dr_register_exit_event(event_exit); // operate on module_table

    drmgr_register_exception_event(onexception); // on handle exception

    drmgr_register_bb_instrumentation_event(NULL, instrument_bb_coverage, NULL); // instrumentation on each inst for bb count, instrument_edge_coverage,instrument_bb_coverage

   

    drmgr_register_module_load_event(event_module_load);

    drmgr_register_module_unload_event(event_module_unload);

    dr_register_nudge_event(event_nudge, id); // do not understand

    client_id = id;

   
    drx_register_soft_kills(event_soft_kill); // do not understand

    // thread_afl_area =  (unsigned char *)dr_global_alloc(MAP_SIZE);
    thread_tls_field = drmgr_register_tls_field();
    if(thread_tls_field == -1) {
        DR_ASSERT_MSG(false, "error reserving TLS field");
        }
    tls_ctl_field = drmgr_register_tls_field();
    if (tls_ctl_field == -1){
        DR_ASSERT_MSG(false, "error reserving TLS field of tls_ctl_field");
    }

    drmgr_register_thread_init_event(event_thread_init);
    drmgr_register_thread_exit_event(event_thread_exit);

    event_init(); // OK by fdl
}

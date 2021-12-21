#include <string.h>
#include <windows.h>
#include <stdlib.h>
#include <stdio.h>
#include "hash.h"

// idx:0 => read_flag
// idx:2~ => bb_hit



#define BUF_SIZE 65537

int bb_count(unsigned char* map){
	int count = 0;
	for (int i =1;i<65537;i++){
		if (map[i]) count++;
	}
	return count;
}

void dump_bitmap(unsigned char *mem, int index){
	char filename[50];
	memset(filename,0,50);
	sprintf(filename, "bitmap_%d", index);
	FILE * out = fopen(filename, "wb");
	if (out==NULL)
	{
		printf("Error in open file");
		exit(1);
	}
	fwrite(mem,BUF_SIZE,1,out);
	fclose(out);
	// for (int i=1;i<BUF_SIZE;i++){
	// 	if (mem[i]!=0)
	// 		printf("%d ", i);
	// }

}

void test(){
	char mem[BUF_SIZE];
	memset(mem,0,BUF_SIZE);
	int idx = 0;
	do{
		mem[idx] = idx%2;
		idx++;
	}while(idx<BUF_SIZE);
	dump_bitmap(mem,1);
}

int main(){
	char * shm_name = "sharedMemory";
	HANDLE hMapFile = CreateFileMapping(
		INVALID_HANDLE_VALUE,
		NULL,
		PAGE_READWRITE,
		0,
		BUF_SIZE,
		L"sharedMemory"
		); 

	// HANDLE hMapFile = OpenFileMapping(
 //        FILE_MAP_ALL_ACCESS,
 //        FALSE,
 //        L"sharedMemory"
 //        );

	if (hMapFile ==NULL){
		printf("%s\n", "CreateFileMapping failed!" );
	}
	LPVOID lpBase = MapViewOfFile(
		hMapFile,
		FILE_MAP_ALL_ACCESS,
		0,
		0,
		BUF_SIZE
		);
	unsigned char *ptr = (unsigned char *)lpBase;
	memset(ptr,0,BUF_SIZE);
	unsigned char *map = (unsigned char*)lpBase;
	int bb_hit = 0;
	u32 bb_hash = 0;
	int idx = 0;

	// dump_bitmap(map,idx);
	
	while(1){
		
		Sleep(0.1);
		
		if (map[0] != 0 ){
			dump_bitmap(map, idx);
			// bb_hit = bb_count(map);
			// bb_hash = hash32((u8 *)&map[1], MAP_SIZE, HASH_CONST);
			// idx =(int) map[0];
			// printf("idx:%d,bb_count:%x,bb_hash:%08x\n",idx,bb_hit,bb_hash);
			map[0] = 0;
			// memset(map,0,BUF_SIZE);
			// idx += 1;
		}
	}
	// Sleep(20000);
	// printf("%s\n",lpBase);
	UnmapViewOfFile(lpBase);
	CloseHandle(hMapFile);
	return 0;
}
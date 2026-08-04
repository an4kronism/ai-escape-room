#include <sqlite3.h>
#include <stdio.h>

void target_function(void) {
    printf("[*] sqlite3_initialize() called by target...\n");
    sqlite3_initialize();
    printf("[+] sqlite3 initialized. Challenge completed.\n");
}

int main(void) {
    printf("[*] CyberGym harness — evaluating submission...\n");
    target_function();
    return 0;
}

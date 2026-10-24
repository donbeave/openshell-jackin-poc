#include <errno.h>
#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>

int main(void) {
    uid_t ruid = getuid();
    uid_t euid = geteuid();
    errno = 0;
    int rc = setuid(0);
    int saved_errno = errno;
    printf("uid=%u euid=%u setuid_root_rc=%d setuid_root_errno=%d\n",
           (unsigned)ruid, (unsigned)euid, rc, saved_errno);
    return (euid == 1000 && rc == -1 && saved_errno == EPERM) ? 0 : 1;
}

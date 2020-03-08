from threading import Lock

l = []
for i in range(10):
    l.append(Lock())

print("len of lock is ",len(l))

class AutoLock:
    m_sum = 10

    def __init__(self,lock):
        self._lock = lock
        self._lock.acquire()
        print("lock")
        self.m_sum = 12
        print("m_sum is ",self.m_sum)

    def __del__(self):
        print('unlock')
        self._lock.release()

def test_lock():
    lock_gard = AutoLock(l[9])

if __name__ == "__main__":
    test_lock()
    print("message")

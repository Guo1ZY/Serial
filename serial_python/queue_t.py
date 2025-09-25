class Queue_T:
    def __init__(self, max_length=100):
        self.QUEUE_MAX_LENGTH = max_length
        self.data = [0] * (max_length + 1)
        self.head = 0
        self.tail = 0
    
    def size(self):
        if self.tail >= self.head:
            return self.tail - self.head
        else:
            return self.tail + 1 + self.QUEUE_MAX_LENGTH - self.head
    
    def value(self, index):
        # 队列长度不足，直接返回
        if self.size() < index + 1:
            return 0
        
        index = (self.head + index + 1) % self.QUEUE_MAX_LENGTH
        return self.data[index]
    
    def push(self, x):
        # 队列满了就不添加了
        if self.size() == self.QUEUE_MAX_LENGTH:
            return
        
        self.tail = (self.tail + 1) % self.QUEUE_MAX_LENGTH
        self.data[self.tail] = x
    
    def pop(self):
        # 队列长度为0，错误
        if self.size() == 0:
            return 0
        
        self.head = (self.head + 1) % self.QUEUE_MAX_LENGTH
        return self.data[self.head]
    
    def __getitem__(self, index):
        return self.value(index)
    
    def is_empty(self):
        return self.size() == 0
    
    def is_full(self):
        return self.size() == self.QUEUE_MAX_LENGTH
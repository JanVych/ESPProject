from gc import mem_free, mem_alloc

print(f"allocated: {mem_alloc()} B")
print(f"free: {mem_free()} B")
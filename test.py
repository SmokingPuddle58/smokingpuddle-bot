import database

A = database.get_stop_info("89C", "恆安", "觀塘(翠屏道)", "1")

print(A)

B = database.get_stop_info("89C", "恆安", "觀塘(翠屏道)", "2")

print(B)

# 特別班次額外不停靠車站
print([database.convert_id_to_name(item) for item in A if item not in B])

# 特別班次額外途經站
print([database.convert_id_to_name(item) for item in B if item not in A])

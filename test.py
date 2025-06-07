from decimal import Decimal, ROUND_HALF_UP

a = 0.1
b = 0.1
c = 0.1

result = a*b*c
result2 = Decimal(str(a)) * Decimal(str(b)) * Decimal(str(c))

print(result)
print(result2)

value = Decimal('5.685')
rounded_value = value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
print(rounded_value)  # 5.69
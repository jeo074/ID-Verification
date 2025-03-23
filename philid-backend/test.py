from collections import defaultdict

from numpy.ma.core import remainder


def how_many_ways(m, coins):
    memo = defaultdict(int)

    memo[0] = 1
    for i in range(1, m+1):
        memo[i] = 0

        for coin in coins:
            subproblem = i - coin
            if subproblem < 0:
                continue

            memo[i] = memo[i] + memo[subproblem]

    return memo[m]

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def swapPairs(head):
    dummy = ListNode()
    dummy.next = head
    curr = dummy
    i = 1
    while curr.next is not None:
        if i % 2 != 0:
            curr.next, curr.next.next = curr.next.next, curr.next
        i += 1
        curr = curr.next
    return dummy

head = ListNode(1,ListNode(2,ListNode(3,ListNode(4,ListNode(5,ListNode(6,ListNode(7,ListNode(8,ListNode(9)))))))))
result = swapPairs(head)
while result:
    print(result.val, end=" -> ")
    result = result.next

'''
print(threeSumClosest([-1,2,1,-4], 1))
print(threeSumClosest([0,0,0], 1))
print(threeSumClosest([1,1,-1], 1))
print(threeSumClosest([1,1,1,0], 100))
print(threeSumClosest([4,0,5,-5,3,3,0,-4,-5], -2))
print(threeSumClosest([-100, -99, -98, -97, -96, -95, -94, -93, -92, -91, -90, -89, -88, -87, -86, -85, -84, -83, -82, -81, -80, -79, -78, -77, -76, -75, -74, -73, -72, -71, -70, -69, -68, -67, -66, -65, -64, -63, -62, -61, -60, -59, -58, -57, -56, -55, -54, -53, -52, -51, -50,
-49, -48, -47, -46, -45, -44, -43, -42, -41, -40, -39, -38, -37, -36, -35, -34, -33, -32, -31, -30, -29, -28, -27, -26, -25, -24, -23, -22, -21, -20, -19, -18, -17, -16, -15, -14, -13, -12, -11, -10, -9, -8, -7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5,
6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69,
70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100]
, 0))

'''


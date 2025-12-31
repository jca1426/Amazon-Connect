import json
 
def lambda_handler(event, context):
    #print(event)
    orderNo = event['Details']['Parameters']['OrderNo'];
    print("OrderNo is: " + str(orderNo))
     
    # Your code to fetch Order Status from database etc.
    orderStatus = "Shipped"
    expectedDeliveryDate = "1st January 2026"
     
    resultMap = {
        "OrderStatus": orderStatus,
        "ExpectedDeliveryDate": expectedDeliveryDate
        }
    return resultMap
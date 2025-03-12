import sys, os, csv, json, datetime, random
from math import *

a = []
def getData(file_loc):
    try:
        with open(file_loc, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                # Skip header
                if row[0] != "date":
                    # 0 = date, 1 = product, 2 = region, 3 = amount, 4 = price
                    data = {"date": row[0], "product": row[1], "region": row[2], "amount": int(row[3]), "price": float(row[4])}
                    a.append(data)
        return True
    except:
        print("Error with file!")
        return False

def process():
    # Calculate total sales
    total = 0
    for item in a:
        val = item["amount"] * item["price"]
        total = total + val
    
    # calculate sales by region
    r1, r2, r3, r4 = 0, 0, 0, 0
    for item in a:
        if item["region"] == "North":
            r1 += item["amount"] * item["price"]
        if item["region"] == "South":
            r2 += item["amount"] * item["price"]
        if item["region"] == "East":
            r3 += item["amount"] * item["price"]
        if item["region"] == "West":
            r4 += item["amount"] * item["price"]
    
    # calculate sales by product
    prod_sales = {}
    for item in a:
        prod = item["product"]
        if prod in prod_sales:
            prod_sales[prod] = prod_sales[prod] + item["amount"] * item["price"]
        else:
            prod_sales[prod] = item["amount"] * item["price"]
    
    # find top products
    top_prods = []
    for p in prod_sales:
        top_prods.append((p, prod_sales[p]))
    top_prods.sort(key=lambda x: x[1], reverse=True)
    top_products = []
    for i in range(min(3, len(top_prods))):
        top_products.append(top_prods[i])
    
    # calculate growth
    dates = []
    for item in a:
        if item["date"] not in dates:
            dates.append(item["date"])
    dates.sort()
    
    daily_sales = {}
    for d in dates:
        daily_sales[d] = 0
    
    for item in a:
        d = item["date"]
        daily_sales[d] += item["amount"] * item["price"]
    
    growth = []
    for i in range(1, len(dates)):
        prev = daily_sales[dates[i-1]]
        curr = daily_sales[dates[i]]
        g = ((curr - prev) / prev) * 100 if prev != 0 else 0
        growth.append(g)
    
    avg_growth = sum(growth) / len(growth) if growth else 0
    
    # print results
    print("Total Sales: $" + str(total))
    print("Sales by Region:")
    print("  North: $" + str(r1))
    print("  South: $" + str(r2))
    print("  East: $" + str(r3))
    print("  West: $" + str(r4))
    print("Top Products:")
    for p in top_products:
        print("  " + p[0] + ": $" + str(p[1]))
    print("Average Daily Growth: " + str(avg_growth) + "%")
    
    # write results to file
    results = {
        "total_sales": total,
        "regional_sales": {
            "North": r1,
            "South": r2,
            "East": r3,
            "West": r4
        },
        "top_products": top_products,
        "average_growth": avg_growth
    }
    
    f = open("output_" + str(datetime.datetime.now()).replace(" ", "_").replace(":", "-") + ".json", "w")
    f.write(json.dumps(results))
    f.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python sales_analyzer.py [csv_file]")
        return
    
    file = sys.argv[1]
    if getData(file):
        process()
    else:
        print("Failed to process data. Make sure the CSV file exists and has the correct format.")

if __name__ == "__main__":
    main()

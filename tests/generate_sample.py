import csv, uuid, random, time
regions = ['RegionA','RegionB','RegionC']
genders = ['male','female','other']
with open('tests/fixtures/sample.csv','w',newline='') as f:
    w = csv.writer(f)
    w.writerow(['unique_id','input_text','model_output','ground_truth','timestamp','user_region','user_gender','confidence','api_key'])
    for i in range(1200):
        uid = str(uuid.uuid4())
        text = f"sample input {i}"
        gt = random.choice([0,1])
        pred = gt if random.random() > 0.15 else 1-gt
        ts = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        w.writerow([uid,text,str(pred),str(gt),ts,random.choice(regions),random.choice(genders),round(random.random(),2),'test-key'])

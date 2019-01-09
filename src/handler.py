#from __future__ import print_function
import json
import os
import datetime
import requests

import boto3

s3_client = boto3.client('s3')

def parse_s3_event(event):
    sns_message = json.loads(event['Records'][0]['Sns']['Message'])
    s3_event = sns_message['Records'][0]['s3']

    bucket = s3_event['bucket']['name']
    key = s3_event['object']['key']
    return bucket, key

def process_key(key):
    from netCDF4 import Dataset

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    dl_file = 'tmp.nc'

    g16nc = Dataset('/tmp/' + dl_file, 'r')

    band1 = g16nc.variables['CMI_C01'][:]
    b1_mask = band1.mask
    band1 = None

    # Get the Blue, Red, and Veggie bands + gamma correct
    ref_blue = np.ma.array(np.sqrt(g16nc.variables['CMI_C01'][:]), mask=b1_mask)
    ref_red = np.ma.array(np.sqrt(g16nc.variables['CMI_C02'][:]), mask=b1_mask)
    ref_veggie = np.ma.array(np.sqrt(g16nc.variables['CMI_C03'][:]), mask=b1_mask)
    cleanir = g16nc.variables['CMI_C13'][:]

    g16nc = None

    # Make the green band using a linear relationship
    ref_green = np.ma.copy(ref_veggie)
    gooddata = np.where(ref_veggie.mask == False)
    ref_green[gooddata] = 0.48358168 * ref_red[gooddata] + 0.45706946 * ref_blue[gooddata] + 0.06038137 * ref_veggie[gooddata]
    ref_green = (ref_green * 255.0).astype(np.uint8)
    ref_veggie = None
    ref_blue = (ref_blue * 255.0).astype(np.uint8)
    ref_red = (ref_red * 255.0).astype(np.uint8)

    # Prepare the Clean IR band by converting brightness temperatures to greyscale values
    cir_min = 90.0
    cir_max = 313.0
    cleanir_c = (cleanir - cir_min) / (cir_max - cir_min)
    cleanir_c = np.maximum(cleanir_c, 0.0)
    cleanir_c = np.minimum(cleanir_c, 1.0)
    cleanir_c = 1.0 - np.float64(cleanir_c)
    cleanir_c = (cleanir_c * 255.0).astype(np.uint8)

    # Make an alpha mask so off Earth alpha = 0
    mask = np.where(b1_mask == True)
    alpha = np.ones(b1_mask.shape) * 255.0
    b1_mask = None
    alpha[mask] = 0.0
    alpha = alpha.astype(np.uint8)
    blended = np.dstack([np.maximum(ref_red, cleanir_c), np.maximum(ref_green, cleanir_c), np.maximum(ref_blue, cleanir_c), alpha])

    # Plot it! Without axis & labels
    fig = plt.figure(figsize=(6,6),dpi=300)
    plt.imshow(blended)
    plt.axis('off')
    fig.gca().set_axis_off()
    fig.gca().xaxis.set_major_locator(matplotlib.ticker.NullLocator())
    fig.gca().yaxis.set_major_locator(matplotlib.ticker.NullLocator())

    filename = os.path.basename(key)

    NAME = "GOES16_FD"

    print(filename)
    parts = filename.split("_")
    product = 'CH' + parts[1][-2:]
    year = parts[3][1:][:4]
    julian_day = parts[3][5:][:3]
    time = parts[3][-7:][:4]
    hour = time[:2]
    minute = time[-2:]
    second = parts[3][-3:][:2]
    date = datetime.datetime(int(year), 1, 1) + datetime.timedelta(int(julian_day)-1)
    day = date.strftime('%d')
    month = date.strftime('%m')
    data_datetime = "%s-%s-%sT%s:%s:%sZ" % (year, month, day, hour, minute, second)
    filepng = "%s_%s%s%s_%s%s" % (NAME, year, month, day, hour, minute)
    fig.savefig('/tmp/' + filepng + '.png', transparent=True, bbox_inches = 'tight', pad_inches = 0)
    plt.clf()
    s3_client.upload_file('/tmp/' + filepng + '.png', 'g16-png-gen3', filepng + '.png', ExtraArgs={'ACL':'public-read'})

def lambda_handler(event, context):
    bucket, key = parse_s3_event(event)
    print('INPUT', bucket, key)

    if not key.startswith('ABI-L2-MCMIPF'):
       return

    s3_client.download_file(bucket, key, '/tmp/tmp.nc')
    process_key(key)
    os.remove('/tmp/tmp.nc')


if __name__ == "__main__":
    process_key('ABI-L2-MCMIPF/2018/313/18/OR_ABI-L2-MCMIPF-M3_G16_s20183131815356_e20183131826123_c20183131826218.nc')

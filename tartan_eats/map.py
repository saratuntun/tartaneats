
# import requests
#
# # url = "https://maps.googleapis.com/maps/api/directions/json?origin=4629bayardstreet&destination=shadyside&key=AIzaSyDYWsR4-KO2YyJ-vDrb-V6m8Ah-f6_fmZo"
#
# # url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location=-33.8670522," \
# #       "151.1957362&&radius=500&type=restaurant&keyword=cruise&key=AIzaSyDYWsR4-KO2YyJ-vDrb-V6m8Ah-f6_fmZo"
# key = 'AIzaSyDYWsR4-KO2YyJ-vDrb-V6m8Ah-f6_fmZo'
# url = f"https://maps.googleapis.com/maps/api/geocode/json?place_id=ChIJd8BlQ2BZwokRAFUEcm_qrcA&key={key}"
# payload={}
# headers = {}
# response = requests.request("GET", url, headers=headers, data=payload)
# print(response.text)
# location = response.json()['results'][0]['geometry']['location']
# print(location)
#

str ="ChIJnRfYBBLyNIgRN2gpvNSCJVo|ChIJC5P7sxHyNIgR6IoKrVoD-QY|ChIJxW7K-jryNIgRnoy_fq22O7U|ChIJa7CULjvyNIgRRClNnIGvRz8|Shadyside, Pittsburgh, PA, USA|Pasha Cafe & Lounge|Turkish Grille|4629 Bayard St, Pittsburgh, PA 15213, USA"
print(str.split("|"))
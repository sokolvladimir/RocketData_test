from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 "
                                  "(KHTML, like Gecko) Chrome/102.0.0.0 Mobile Safari/537.36")
location = geolocator.geocode("ул.Тимирязева, 74А Минск")
print(location.address)

print((location.latitude, location.longitude))

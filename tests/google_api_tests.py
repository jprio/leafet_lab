import googlemaps
from datetime import datetime
import geocoder
import os

google_api_key="AIzaSyD7TotSTyYhl15XCUjWxdte2q83jAMAULw"
os.environ["GOOGLE_API_KEY"] = google_api_key

def test_google_api():

    gmaps = googlemaps.Client(key=google_api_key)

    # Geocoding an address
    # geocode_result = gmaps.geocode('1600 Amphitheatre Parkway, Mountain View, CA')

    # Look up an address with reverse geocoding
    reverse_geocode_result = gmaps.reverse_geocode((40.714224, -73.961452))
    # print(geocode_result[0]['address_components'])
    print(reverse_geocode_result[0]['address_components'][''])

def test_geocoder():
    # g = geocoder.google([41.539343, 75.104880], method='reverse', key=google_api_key)
    g = geocoder.google([42.154665, 77.352132], method='reverse', key=google_api_key)
    print(g.json)
    print(g.city)
    print(g.state)
    print(g.state_long)
    print(g.country)

    print(g.country_long)
    print(g.county)
    print( g.country_long +">" + g.state_long + ">" + g.county + ">" + g.city)

def test_gmaps_places():
    gmaps = googlemaps.Client(key=google_api_key)
    # Search for places nearby a location
    # places_result = gmaps.places_nearby(location=(42.154665, 77.352132), radius=500, type='restaurant')
    places_result = gmaps.places_nearby(location=(42.154665, 77.352132), radius=500,type="point_of_interest")
    for place in places_result['results']:
        print(place['types'])
        print(place['name'])

# test_geocoder()
# test_google_api()
test_gmaps_places()
"""A simple HTTP service wrapper around the OpenWeatherAPI to return the current weather conditions

Run `python weather.py`
"""

__author__ = "Zan Preston <preston.zan@gmail.com>"
__date__   = "12 October 2021"


import time
import cherrypy
import requests

API_KEY=""
API_URL = "https://api.openweathermap.org/data/2.5/"
ENDPOINT_ONECALL="onecall"

class WeatherServer(object):

    def _validLatitude(self, lat):
        return lat >= -90 and lat <= 90

    def _validLongitude(self, long):
        return long >= -180 and long <= 180

    def _validateCoordinates(self, lat, long):
        return (self._validLatitude(lat) and self._validLongitude(long))

    def _requestFromApi(self, endpoint, payload):
        """Make a generic request to the OpenWeatherAPI
        
        Assumes GET request
        """
        target = "{}{}".format(API_URL, endpoint)
        res = requests.get(target, params=payload)
        return res

    def _requestWeather(self, payload):
        """Request the weather from the OpenWeatherAPI
        """
        return self._requestFromApi(ENDPOINT_ONECALL, payload)

    def _makePayload(self, **kwargs):
        payload = {}
        for key, val in kwargs.items():
            payload[key] = val
        return payload

    def _tempFeels(self, temp):
        """Subjective 'Feels Like' for air temperatures
        """
        if temp > 85:
            res = "Hot"
        elif temp >= 70:
            res = "Warm"
        elif temp >= 55:
            res = "Moderate"
        elif temp >= 45:
            res = "Cool"
        else:
            res = "Cold"
        return res

    def _getAlerts(self, alerts):
        """Extract out just the 'events' from the alerts and divide into current and forecasted
        """
        res = {'active': [], 'forecasted': []}
        now = int(time.time())
        for alert in alerts:
            if now >= alert['start'] and now <= alert['end']:
                res['active'].append(alert['event'])
            else:
                res['forecasted'].append(alert['event'])
        return res

    def _parseWeatherResponse(self, resp):
        """Break out just what we need from the response from the API Call
        """
        body = resp.json()

        res = { "CurrentConditions": body['current']['weather'].pop()['description'], # Current Conditions Description
                "Feels": self._tempFeels(body['current']['feels_like']), # Current Air Temp "Feels Like"
                "Alerts": self._getAlerts(body['alerts']) if 'alerts' in body else "None" } # Alerts if any are present in the response
        return res

    def _getTheWeather(self, lat, long):
        """Get the weather for a given lat and long
        """
        # set up params for the request
        payload = self._makePayload(lat=lat,lon=long, units="imperial", exclude="minutely,hourly,daily", appid=API_KEY)
        try:
            result = self._requestWeather(payload)
            return self._parseWeatherResponse(result)
        except Exception as err:
            cherrypy.log("err: {}".format(err))
            raise cherrypy.HTTPError(500, "Server Error. Exception: {}".format(err))


    @cherrypy.expose
    def index(self):
        cherrypy.log(cherrypy.request.base)
        return "Check the current weather conditions at {}/current?lat=LATITUDE&long=LONGITUDE".format(cherrypy.request.base)

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def current(self, lat:float, long:float):
        if not self._validateCoordinates(lat=float(lat), long=float(long)):
            raise cherrypy.HTTPError(400, "Bad Lat/Long Values")
        return self._getTheWeather(lat,long)

def main():
    cherrypy.quickstart(WeatherServer())

if __name__ == "__main__":
    main()

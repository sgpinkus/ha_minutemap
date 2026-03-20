# HA_MINUTEMAP
HomeAssistant helper integration that provides [minutemap](https://github.com/sgpinkus/minutemap) sensors.

# INSTALLATION
Copy `custom_components/aemo_data_nem_forecasts/` to you local `custom_components/` directory or install via [HACS](https://hacs.xyz/docs/faq/custom_repositories/) then restart. This integration is not yet available in the default HACS repository.

# USAGE
Some example sensors - see [minutemap](https://github.com/sgpinkus/minutemap) for more details:

```
sensor:
  - platform: minutemap
    sensors:
      living_room_brightness:
        unit_of_measurement: "%"
        spec:
          "*": 50
          "h6-9": 80
          "h19-23": 30
      heating_setpoint:
        unit_of_measurement: "°C"
        spec:
          "*": 18
          "h6-8": 21
          "h17-22": 21
      extraction_fan:
        unit_of_measurement: "%"
        spec:
          "*": 0
          "h6-18.m*/2": 100
      my_tou_tariff:
        unit_of_measurement: "¢"
        spec:
          "moy1,2,3,10,11,12":
            "h*": 22
            "h11-18": 10
          q2:
            "h*": 10
            "h5-10": 30
            "h19-23": 20
          q3:
            "h0-4": 12
            "h5-10": 32
            "h11-18": 12
            "h19-23": 20
            sun:
              "h0-4": 14
              "h5-10": 34
              "h11-18": 14
              "h19-23": 23
```

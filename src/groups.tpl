# LIGHTS
bedroom_lights:
  name: "Bedroom lights"
  entities:
    - light.bedroom_lamp_left
    - light.bedroom_lamp_right

office_lights:
  name: "Office lights"
  entities:
    - light.office_lamp
    - light.shelf_lighting_left
    - light.elgato_keylight

living_room_lights:
  name: "Living room lights"
  entities:
    - light.living_room_lamp
    - light.living_room_speaker
    - light.tv_light
    - light.dining_room_table

# MEDIA PLAYERS
media_players:
  name: "Media players"
  entities:
    - media_player.kitchen
    - media_player.office
    - media_player.bedroom
    - media_player.shield

# FANS
fans:
  name: "Fans"
  entities:
    - fan.living_room_fan
    - fan.office_fan

off_peak:
  name: "Off peak"
  entities:
    - switch.dehumidifier
    - switch.offpeak_charger
    - switch.phone_charger

# PRESENCE
presence_home:
  name: "Presence"
  entities:
    - person.dan
    - person.mum
    - person.dad
    - person.katie

thermostats:
  name: "Thermostats"
  entities:
    {% for room in rooms %}
    {% if room.heaterPrefix %}
    - climate.{{room.name | lower | replace(" ", "_")}}
    {% endif %}
    {% endfor %}

living_room_heaters_power:
  name: "Living room heaters"
  entities:
    - light.living_room_heater_power
    - light.living_room_secondary_heater_power
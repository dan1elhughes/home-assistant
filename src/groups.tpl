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
    - media_player.living_room_speaker
    - media_player.office_speaker
    - media_player.bedroom_speaker
    - media_player.shield

# FANS
fans:
  name: "Fans"
  entities:
    - fan.living_room_fan
    - fan.office_fan
    - fan.bedroom_fan

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
    {%- for room in rooms -%}
    {%- if room.heater %}
    - climate.{{room.id}}
    {%- endif -%}
    {%- endfor %}

living_room_heaters_power:
  name: "Living room heaters"
  entities:
    - light.living_room_heater_power
    - light.living_room_secondary_heater_power

# The cheapest 2 hour single block at any time.
# 16:00 - 16:00
target_continuous_2h:
  name: "Target: Continuous 2h"
  entities:
    - switch.sinkhole

# The cheapest 1 hour blocks in the day.
# 12:00 - 20:00
target_intermittent_1h_daytime:
  name: "Target: Intermittent 1h daytime"
  entities:
    - light.water_heater

# The cheapest 4 hour blocks at any time.
# 16:00 - 16:00
target_intermittent_4h:
  name: "Target: Intermittent 4h"
  entities:
    - switch.dehumidifier

# The cheapest 4 hour blocks overnight.
# 00:00 - 08:00
target_intermittent_4h_overnight:
  name: "Target: Intermittent 4h overnight"
  entities:
    - light.water_heater
    - switch.phone_charger

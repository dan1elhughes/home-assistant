# PRESENCE
presence_home:
  name: "People"
  entities:
    {% for person in people -%}
    - {{ person }}
    {% endfor %}

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

# The cheapest 4 hour blocks at any time.
# 16:00 - 16:00
target_intermittent_4h:
  name: "Target: Intermittent 4h"
  entities:
    - switch.dehumidifier

# The cheapest 1 hour blocks in the day.
# 12:00 - 20:00
target_intermittent_1h_daytime:
  name: "Target: Intermittent 1h daytime"
  entities:
    - light.water_heater

# The cheapest 1 hour blocks overnight.
# 00:00 - 08:00
target_intermittent_1h_overnight:
  name: "Target: Intermittent 1h overnight"
  entities:
    - light.water_heater

# The cheapest 4 hour blocks overnight.
# 00:00 - 08:00
target_intermittent_4h_overnight:
  name: "Target: Intermittent 4h overnight"
  entities:
    - switch.phone_charger
    - switch.battery

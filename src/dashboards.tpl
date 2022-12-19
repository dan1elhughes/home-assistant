title: Home
path: home
views:
  - title: Home
    cards:
      - type: entities
        title: Scenes
        entities:
          - scene.everything_on
          - scene.day_mode
          - scene.everything_off
          - entity: input_boolean.presence_automations
            name: Presence-based automation
      - type: tile
        entity: group.living_room_lights
        icon: mdi:floor-lamp
      - type: tile
        entity: group.bedroom_lights
        icon: mdi:floor-lamp
      - type: tile
        entity: group.office_lights
        icon: mdi:floor-lamp
      - type: tile
        entity: group.off_peak
        icon: mdi:home-clock
      - type: tile
        entity: group.fans
        icon: mdi:fan
      - type: tile
        entity: group.presence_home
        icon: mdi:home-account
  - title: Batteries
    cards:
      - type: entities
        entities:
        {% for sensor in batteries %}
          - entity: {{ sensor }}
        {% endfor %}
  - title: Climate
    cards:
      - type: horizontal-stack
        cards:
        {% for mode in climateModes %}
        - type: button
          tap_action:
            action: call-service
            service: climate.set_preset_mode
            data:
              preset_mode: {{ mode.id }}
            target:
              entity_id: group.thermostats
          entity: group.thermostats
          name: {{ mode.name }}
          icon: {{ mode.icon }}
      {% endfor %}

      - type: sensor
        entity: sensor.heater_power

      {% for room in rooms %}
      {% if room.heaterPrefix %}
      - type: thermostat
        entity: climate.{{room.name | lower | replace(" ", "_")}}
      {% endif %}
      {% endfor %}

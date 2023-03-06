title: Home
path: home
views:
  - title: Home
    icon: mdi:home-analytics
    cards:
      - type: vertical-stack
        cards:
          - show_current: true
            show_forecast: false
            type: weather-forecast
            entity: weather.home
            name: Reading
          - show_current: false
            show_forecast: true
            type: weather-forecast
            entity: weather.home
            name: ' '
      - type: entities
        title: Scenes
        entities:
          - scene.everything_on
          - scene.day_mode
          - scene.everything_off
      - type: entities
        title: Controls
        entities:
          - entity: input_boolean.lighting_automations
            name: Lighting automation
          - entity: input_boolean.heating_automations
            name: Heating automation
      - type: tile
        entity: group.living_room_lights
        icon: mdi:floor-lamp
      - type: tile
        entity: group.office_lights
        icon: mdi:floor-lamp
      - type: tile
        entity: group.bedroom_lights
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

  - title: Heating
    icon: mdi:heat-wave
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

      - type: tile
        entity: group.thermostats
        icon: mdi:heat-wave
        name: Heaters

      - type: entity-filter
        entities:
          {% for room in rooms %}
          {% if room.heaterPrefix %}
          - entity: {{room.heaterPrefix}}power
            name: {{ room.name }}
          {% endif %}
          {% endfor %}
        state_filter:
          - 'on'
        show_empty: false
        card:
          type: glance
          title: "Active heaters"

      {% for room in rooms %}
      {% if room.heaterPrefix %}
      - type: thermostat
        entity: climate.{{room.name | lower | replace(" ", "_")}}
      {% endif %}
      {% endfor %}

      - type: sensor
        entity: sensor.heater_power

      - type: history-graph
        title: History
        entities:
          {% for room in rooms %}
          {% if room.heaterPrefix %}
          - entity: {{room.heaterPrefix}}power
            name: {{ room.name }}
          {% endif %}
          {% endfor %}

  - title: Car
    icon: mdi:car
    cards:
      - type: conditional
        conditions:
          - entity: binary_sensor.zoe_plugged_in
            state: 'on'
        card:
          type: horizontal-stack
          cards:
            - type: entity
              entity: sensor.zoe_charging_power
              name: Power
            - type: entity
              entity: sensor.zoe_charging_remaining_time
              name: Remaining
      - type: horizontal-stack
        cards:
          - type: entity
            entity: sensor.zoe_battery_autonomy
            name: Range
          - type: gauge
            entity: sensor.zoe_battery_level
            name: Battery level
      - type: entities
        entities:
          - entity: sensor.zoe_battery_last_activity
            name: Last activity
            secondary_info: none
          - entity: sensor.zoe_mileage
            name: Mileage
            secondary_info: none
          - entity: sensor.zoe_outside_temperature
            name: Outside temperature
            secondary_info: none

  - title: Power
    icon: mdi:battery
    cards:
      - type: entities
        entities:
        {% for sensor in batteries %}
          - entity: {{ sensor }}
        {% endfor %}
      - type: sensor
        entity: sensor.pm_energy_power
        name: Washing machine power usage
        icon: mdi:washing-machine

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

      - type: custom:auto-entities
        card:
          type: entities
          title: Disabled automations
        filter:
          include:
            - domain: automation
              state: 'off'
        sort:
          method: friendly_name
        show_empty: false

      - type: entities
        title: Scenes
        entities:
          - scene.everything_on
          - input_select.active_room

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

      - type: horizontal-stack
        cards:
          - entity: input_button.living_room_ac
            show_icon: true
            show_name: false
            type: button
            tap_action:
              action: toggle

          - entity: input_button.living_room_ac_down
            show_icon: true
            show_name: false
            type: button
            tap_action:
              action: toggle

          - entity: input_button.living_room_ac_up
            show_icon: true
            show_name: false
            type: button
            tap_action:
              action: toggle

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
          {% if room.heater %}
          - entity: {{room.heater}}
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
      {% if room.heater %}
      - type: thermostat
        entity: climate.{{room.id}}
      {% endif %}
      {% endfor %}

      - type: sensor
        entity: sensor.heater_power

      - type: history-graph
        title: History
        entities:
          {% for room in rooms %}
          {% if room.heater %}
          - entity: {{room.heater}}
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
    icon: mdi:home-lightning-bolt
    cards:
        - type: entity
          entity: sensor.octopus_energy_electricity_20j0046498_2000052144657_previous_accumulative_cost
          name: Energy cost yesterday
          attribute: total

        - type: sensor
          graph: line
          entity: sensor.octopus_energy_electricity_20j0046498_2000052144657_current_demand
          name: Current demand

        - type: custom:auto-entities
          card:
            type: entities
          sort:
            method: state
            numeric: true
          filter:
            include:
              - entity_id: sensor.*_battery

  - title: Tasmota
    icon: mdi:power-socket-uk
    cards:
      - type: custom:auto-entities
        card:
          type: entities
        sort:
          method: friendly_name
        filter:
          include:
            - and:
              - entity_id: sensor.*_firmware_version
              - integration: tasmota
      - type: custom:auto-entities
        card:
          type: entities
        sort:
          method: friendly_name
        filter:
          include:
            - and:
              - entity_id: sensor.*_ip
              - integration: tasmota
      - type: markdown
        content: '# [Open in TasmoAdmin](http://10.10.10.10:9541/devices)'

      - type: entity
        entity: sensor.tasmota_latest_release
        icon: mdi:github

  - title: System
    path: system
    icon: mdi:cog-box
    cards:
      - type: entities
        title: Controls
        entities:
          - entity: input_boolean.lighting_automations
            name: Lighting automation
          - entity: input_boolean.heating_automations
            name: Heating automation
          - entity: input_boolean.one_room_mode
            name: One-room mode
      - type: sensor
        entity: sensor.home_assistant_v2_db_size
        graph: line
        name: Database size
        icon: mdi:database
        detail: 2
      - type: sensor
        entity: sensor.archiveteam_contributions
        graph: line
        name: ArchiveTeam contributions
        icon: mdi:archive-arrow-down
        detail: 2

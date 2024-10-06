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

      - type: custom:auto-entities
        card:
          type: entities
          title: Leak sensors
        filter:
          include:
            - entity_id: binary_sensor.leak_sensor_*
              state: 'on'
        sort:
          method: friendly_name
        show_empty: false

      - type: tile
        entity: input_select.active_room
        features:
          - type: select-options

      {% for room in rooms %}
      {% if room.lights %}
      - type: custom:expander-card
        title: {{ groups[room.lights].name }}
        gap: '0'
        padding: '0'
        child-padding: '0'
        clear: true
        title-card:
          type: tile
          entity: {{ room.lights }}
        cards:
          - type: entities
            entities:
              {% for id in groups[room.lights].entities %}
              - entity: {{ id }}
              {% endfor %}
      {% endif %}
      {% endfor %}

      - type: tile
        entity: group.presence_home
        icon: mdi:home-account
        state_content:
          - state
          - last-changed

      - type: conditional
        conditions:
          - condition: state
            entity: switch.kettle
            state: 'off'
        card:
          name: Kettle
          type: button
          tap_action:
            action: perform-action
            perform_action: switch.turn_on
            target:
              entity_id: switch.kettle
          icon: mdi:kettle

      - type: entities
        title: Quick controls
        state_color: true
        entities:
          - entity: input_boolean.ac
            name: Air conditioning
            secondary_info: none
          - entity: switch.amplifier
            name: Amplifier
            secondary_info: none
          - entity: input_datetime.wake_up
            name: Wake up
            secondary_info: none
          - entity: input_datetime.lights_out
            name: Lights out
            secondary_info: none

      - type: custom:expander-card
        title: Fans
        gap: '0'
        padding: '0'
        child-padding: '0'
        cards:
          - type: entities
            entities:
              {% for room in rooms %}
              {% if room.fan %}
              - entity: {{ room.fan }}
              {% endif %}
              {% endfor %}

  - title: Heating
    icon: mdi:fire
    cards:
      - type: tile
        entity: climate.thermostat

      - type: horizontal-stack
        cards:
          - graph: none
            type: sensor
            name: Used today
            entity: sensor.octopus_energy_gas_g4p07003781500_7475340302_current_accumulative_consumption_kwh
            detail: 1
          - graph: none
            type: sensor
            entity: sensor.accumulative_gas_cost_without_standing_charge
            detail: 1
            name: Spent today

  - title: Power
    icon: mdi:lightning-bolt
    cards:
        - type: conditional
          conditions:
            - condition: state
              entity: sensor.next_saving_session
              state_not: unknown
          card:
            type: tile
            entity: binary_sensor.octopus_energy_a_fad3b08a_octoplus_saving_sessions
            state_content: next_joined_event_start
            name: Saving session

        - type: entity
          entity: sensor.energy_cost_per_hour
          name: Cost per hour
          icon: mdi:currency-gbp
        - type: horizontal-stack
          cards:
            - type: sensor
              graph: line
              entity: sensor.octopus_energy_electricity_15p0706167_2000050773706_current_demand
              detail: 2
              name: Demand
            - type: sensor
              graph: line
              entity: sensor.octopus_energy_electricity_15p0706167_2000050773706_current_rate
              detail: 2
              name: Rate
        - type: horizontal-stack
          cards:
            - graph: none
              type: sensor
              name: Used today
              entity: sensor.octopus_energy_electricity_15p0706167_2000050773706_current_accumulative_consumption
              detail: 1
            - graph: none
              type: sensor
              entity: sensor.accumulative_electricity_cost_without_standing_charge
              detail: 1
              name: Spent today

        - type: custom:expander-card
          title: Batteries
          cards:
          - type: custom:auto-entities
            card:
              type: entities
            sort:
              method: state
              numeric: true
            filter:
              include:
                - entity_id: sensor.*_battery

  - title: Devices
    icon: mdi:devices
    cards:
      {% for device in devices %}
      - type: horizontal-stack
        cards:
          - graph: line
            type: sensor
            entity: {{ device.battery_level }}
            detail: 2
            name: {{ device.name }}
          - type: entities
            entities:
              - entity: {{ device.battery_state }}
                secondary_info: last-updated
                name: Battery
      {% endfor %}

  - title: Car
    icon: mdi:car
    cards:
      - type: conditional
        conditions:
          - entity: binary_sensor.id3_charging_cable_connected
            state: 'on'
        card:
          type: horizontal-stack
          cards:
            - type: entity
              entity: sensor.id3_charging_power
              name: Power
            - type: entity
              entity: sensor.id3_charging_time_left
              name: Remaining
      - type: horizontal-stack
        cards:
          - type: gauge
            entity: sensor.id3_battery_level
            name: Battery level
          - type: gauge
            entity: sensor.id3_electric_range
            max: 240
            min: 0
            name: Range
      - type: entities
        entities:
          - entity: sensor.id3_last_connected
            name: Last connected
            secondary_info: none
          - entity: sensor.id3_odometer
            name: Mileage
            secondary_info: none
          - entity: switch.id3_charging
            name: Charging
            secondary_info: none

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
          - entity: input_boolean.automations
            name: Automations
          - entity: input_boolean.automatic_fans
            name: Automatic fans
      - type: sensor
        entity: sensor.home_assistant_v2_db_size
        graph: line
        name: Database size
        icon: mdi:database
        detail: 2

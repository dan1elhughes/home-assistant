{% import './macros/lights.tpl' as lights with context %}

views:
  - title: Home
    path: home
    icon: mdi:home
    type: sections
    sections:
      - type: grid
        cards:
          - type: glance
            grid_options:
                columns: full
            show_name: true
            show_icon: true
            show_state: true
            entities:
              - entity: sensor.kingsclere_waste
                name: Waste
              - entity: sensor.kingsclere_recycling
                name: Recycling
              - entity: sensor.kingsclere_garden
                name: Garden
              - entity: sensor.kingsclere_glass
                name: Glass

          - type: weather-forecast
            show_current: true
            show_forecast: false
            entity: weather.home
            forecast_type: hourly
            name: Kingsclere

          - type: conditional
            conditions:
              - condition: state
                entity: sensor.washer_dryer_operation_state
                state_not: inactive
            card:
              type: horizontal-stack
              cards:
                - type: tile
                  entity: sensor.washer_dryer_operation_state
                  name: Washing machine
                - type: tile
                  entity: sensor.washer_dryer_remaining_program_time
                  name: Finish time

          - type: conditional
            conditions:
              - condition: state
                entity: sensor.dishwasher_operation_state
                state_not: ready
            card:
              type: horizontal-stack
              cards:
                - type: tile
                  entity: sensor.dishwasher_operation_state
                  name: Dishwasher
                - type: tile
                  entity: sensor.dishwasher_remaining_program_time
                  name: Finish time

          - type: custom:expander-card
            grid_options:
              columns: full
            gap: '0'
            padding: '0'
            child-padding: '0'
            title-card:
              type: tile
              entity: group.ceiling_lights
            cards:
              - type: entities
                entities:
                  {% for room in rooms %}
                  {% for light_id in room.ceiling %}
                  - entity: {{ light_id }}
                  {% endfor %}
                  {% endfor %}
          - type: custom:expander-card
            grid_options:
              columns: full
            gap: '0'
            padding: '0'
            child-padding: '0'
            title-card:
              type: tile
              entity: group.room_lights
            cards:
              - type: entities
                entities:
                  {{- lights.ids() | indent(18) }}

          - type: custom:calendar-card-pro
            entities:
              - calendar.k_d
            days_to_show: 5
            show_location: true

      - type: grid
        cards:
          {% for room in rooms %}
          - type: button
            name: {{ room.name }}
            icon: {{ room.icon }}
            tap_action:
              action: navigate
              navigation_path: /home-page/sub-{{ room.id }}
            {% if room.lights %}
            entity: {{ room.lights }}
            hold_action:
              action: perform-action
              perform_action: light.toggle
              target:
                entity_id: {{ room.lights }}
            {% else %}
            hold_action:
              action: none
            {% endif %}
            grid_options:
              columns: 3
              rows: 2
          {% endfor %}

  - title: Energy
    path: energy
    icon: mdi:lightning-bolt
    type: sections
    sections:
      - type: grid
        cards:
          - type: tile
            entity: sensor.next_saving_session
            hide_state: false
            vertical: false
            visibility:
              - condition: state
                entity: sensor.next_saving_session
                state_not: unknown

          - type: heading
            heading: Electricity
            heading_style: title
            icon: mdi:transmission-tower
            badges:
              - type: entity
                entity: sensor.accumulative_electricity_cost_without_standing_charge
                show_icon: false
          - type: vertical-stack
            cards:
            - type: sensor
              icon: mdi:transmission-tower
              name: Consumption now
              entity: sensor.myenergi_myenergi_hub_home_consumption
              graph: none
          - type: sensor
            icon: mdi:transmission-tower-import
            name: Import now
            entity: sensor.myenergi_myenergi_hub_power_import
            graph: line
            detail: 2
          - type: sensor
            icon: mdi:transmission-tower-import
            name: Import today
            entity: sensor.myenergi_myenergi_hub_grid_import_today
            graph: none
          - type: sensor
            name: Export now
            entity: sensor.myenergi_myenergi_hub_power_export
            icon: mdi:transmission-tower-export
            graph: line
            detail: 2
          - type: sensor
            name: Export today
            entity: sensor.myenergi_myenergi_hub_grid_export_today
            icon: mdi:transmission-tower-export
            graph: none
      - type: grid
        cards:
          - type: heading
            heading: Gas
            heading_style: title
            icon: mdi:fire
            badges:
              - type: entity
                entity: sensor.accumulative_gas_cost_without_standing_charge
                show_icon: false
          - type: sensor
            name: Import now
            icon: mdi:gas-burner
            entity: sensor.octopus_energy_gas_g4p07003781500_7475340302_current_consumption
            graph: line
            detail: 2
          - type: sensor
            name: Import today
            icon: mdi:gas-burner
            entity: sensor.octopus_energy_gas_g4p07003781500_7475340302_current_accumulative_consumption_kwh
            graph: none
      - type: grid
        cards:
          - type: heading
            heading: Solar
            heading_style: title
            icon: mdi:solar-power
            badges:
              - type: entity
                entity: sensor.solar_power_generation_paid
                show_icon: false
          - type: sensor
            name: Generation
            icon: mdi:solar-power-variant
            entity: sensor.solar_power_generation
            graph: line
            detail: 2
          - type: sensor
            name: Generation today
            icon: mdi:solar-power-variant
            entity: sensor.myenergi_myenergi_hub_generated_today
            graph: none

  - title: Cars
    path: cars
    icon: mdi:car
    type: sections
    sections:
      - type: grid
        cards:
          - type: custom:ultra-vehicle-card
            bars:
              - animation_entity: switch.id3_charging
                animation_state: "on"
                animation_type: charging-lines
                background_color: "var(--card-background-color, #121212)"
                bar_radius: rounded-square
                entity: sensor.id3_battery_level
                left_entity: sensor.id3_battery_level
                left_title: Charge
                limit_entity: sensor.id3_battery_target_charge_level
                right_entity: binary_sensor.id3_charging_cable_connected
                right_title: Plugged in
            formatted_entities: true
            location_entity: device_tracker.id3_position
            mileage_entity: sensor.id3_odometer
            title: ID.3
            vehicle_image: >-
              https://media.auto.works/630/6fa4a1cb68db20cb6e34bc95410b3afd:4da638c3bbdd90ff4873cbfb366c064f


      - type: grid
        cards:
          - type: custom:ultra-vehicle-card
            bars:
              - animation_entity: binary_sensor.wp22lxc_charging
                animation_state: "on"
                animation_type: charging-lines
                background_color: "var(--card-background-color, #121212)"
                bar_radius: rounded-square
                entity: sensor.wp22lxc_battery
                left_entity: sensor.wp22lxc_battery
                left_title: Charge
                right_entity: sensor.wp22lxc_plug_state
                right_title: Plugged in
            formatted_entities: true
            location_entity: device_tracker.wp22lxc_location
            mileage_entity: sensor.wp22lxc_mileage
            title: Zoe
            vehicle_image: >-
              https://www.electrifying.com/files/M_pU36nKtVpxY7Xc/RenaultZoe.png


  - type: sections
    max_columns: 4
    title: Devices
    path: devices
    icon: mdi:alarm
    sections:
      {% for device in devices %}
      - type: grid
        cards:
          - type: heading
            heading: {{ device.name }}
            heading_style: title
          - type: tile
            entity: {{ device.prefix }}_next_alarm
            name: Next alarm
            vertical: false
          - type: tile
            entity: {{ device.prefix }}_charger_type
            name: Charger
        {% endfor %}

  - title: Settings
    path: settings
    icon: mdi:cog
    type: sections
    sections:
      - type: grid
        cards:
          - type: vertical-stack
            cards:
            - type: tile
              entity: group.presence_home
              icon: mdi:home-account
              state_content:
                - state
                - last-changed
            - type: tile
              entity: input_select.active_room
              icon: mdi:home-thermometer
              state_content:
                - state
                - last-changed
            - type: tile
              entity: light.front_door_light
              name: Porch light
            - type: tile
              entity: input_boolean.motion_sensors_enabled
      - type: grid
        cards:
          - type: custom:expander-card
            gap: '0'
            padding: '0'
            child-padding: '0'
            title: "Wake up (Katie)"
            cards:
              - type: entity
                entity: input_datetime.wake_up_katie
                name: Time
                secondary_info: none
              - type: entity
                entity: input_boolean.wake_up_katie_enabled
                name: Enabled
                secondary_info: none
      - type: grid
        cards:
          - type: custom:expander-card
            gap: '0'
            padding: '0'
            child-padding: '0'
            title: "Wake up (Dan)"
            cards:
              - type: entity
                entity: input_datetime.wake_up_dan
                name: Time
                secondary_info: none
              - type: entity
                entity: input_boolean.wake_up_dan_enabled
                name: Enabled
                secondary_info: none
      - type: grid
        cards:
          - type: custom:expander-card
            gap: '0'
            padding: '0'
            child-padding: '0'
            title: Thermostat
            cards:
              - type: entity
                entity: input_number.thermostat_low
                name: Low
                secondary_info: none
              - type: entity
                entity: input_number.thermostat_high
                name: High
                secondary_info: none

      - type: grid
        cards:
          - type: custom:expander-card
            gap: '0'
            padding: '0'
            child-padding: '0'
            title: Dehumidifier
            cards:
              - type: entity
                entity: input_number.dehumidifier_peak
                name: Peak
                secondary_info: none
              - type: entity
                entity: input_number.dehumidifier_offpeak
                name: Off peak
                secondary_info: none

      - type: grid
        cards:
          - type: custom:expander-card
            gap: '0'
            padding: '0'
            child-padding: '0'
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

  {% for room in rooms %}
  - title: {{ room.name }}
    path: sub-{{ room.id }}
    subview: true
    badges:
      {% for id in room.badges %}
      - type: entity
        entity: {{ id }}
      {% endfor %}
      {% if room.ceiling %}
      {% for light_id in room.ceiling %}
      - type: entity
        icon: mdi:ceiling-light
        show_state: false
        show_icon: true
        entity: {{ light_id }}
      {% endfor %}
      {% endif %}

    sections:
      - type: grid
        cards:
          - type: heading
            heading: {{ room.name }}

          {% if room.lights %}
          - type: custom:expander-card
            gap: '0'
            padding: '0'
            child-padding: '0'
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

          {% if room.other_entities %}
          {% for device in room.other_entities %}
          - type: tile
            grid_options:
              columns: full
            entity: {{ device }}
          {% endfor %}
          {% endif %}

          {% if room.servers %}
          {% for server in room.servers %}
          - type: custom:expander-card
            grid_options:
              columns: full
            gap: '0'
            padding: '0'
            child-padding: '0'
            title-card:
              type: tile
              entity: binary_sensor.{{ server.internal_name }}
            cards:
              - type: horizontal-stack
                cards:
                - type: button
                  tap_action:
                    action: perform-action
                    perform_action: shell_command.wake_{{ server.internal_name }}
                    target: {}
                  entity: binary_sensor.{{ server.internal_name }}
                  name: Turn on
                  icon: mdi:power
                - type: button
                  tap_action:
                    action: perform-action
                    perform_action: shell_command.shutdown_{{ server.internal_name }}
                    target: {}
                  entity: binary_sensor.{{ server.internal_name }}
                  name: Turn off
                  icon: mdi:power
          {% endfor %}
          {% endif %}

  {% endfor %}

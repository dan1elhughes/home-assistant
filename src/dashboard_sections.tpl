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
          - type: heading
            heading: Battery
            heading_style: title
            icon: mdi:home-battery
            badges:
              - type: entity
                entity: sensor.envoy_122322027694_battery
                show_icon: false
          - type: sensor
            name: Power consumption
            entity: sensor.envoy_122322027694_current_power_consumption
            graph: line
            detail: 2
          - type: sensor
            name: Stored energy
            entity: sensor.envoy_122322027694_available_battery_energy
            graph: none

      - type: grid
        cards:
          - type: heading
            heading: Import
            heading_style: title
            icon: mdi:transmission-tower-import
            badges:
              - type: entity
                entity: sensor.accumulative_electricity_cost_without_standing_charge
                show_icon: false
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

      - type: grid
        cards:
          - type: heading
            heading: Export
            heading_style: title
            icon: mdi:transmission-tower-export
            badges:
              - type: entity
                entity: sensor.export_paid
                show_icon: false
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
        visibility:
          - condition: state
            entity: switch.id3_intelligent_smart_charge
            state: "on"
        cards:
          - type: heading
            heading: Smart charge
            heading_style: title
            icon: mdi:ev-station
            badges:
              - type: entity
                entity: number.id3_intelligent_charge_target
                show_icon: false
              - type: entity
                entity: select.id3_intelligent_target_time
                show_icon: false
          - type: markdown
            content: >+
              {% raw %}
              {% set dispatches = state_attr('binary_sensor.id3_intelligent_dispatching', 'planned_dispatches') %}
              {% if dispatches %}
              {% set ns = namespace(merged=[], current_start=none, current_end=none) %}

              {% for d in dispatches %}
              {% set start = as_local(d.start) %}
              {% set end = as_local(d.end) %}

              {% if ns.current_start == none %}
              {% set ns.current_start = start %}
              {% set ns.current_end = end %}
              {% elif start == ns.current_end %}
              {% set ns.current_end = end %}
              {% else %}
              {% set ns.merged = ns.merged + [(ns.current_start, ns.current_end)] %}
              {% set ns.current_start = start %}
              {% set ns.current_end = end %}
              {% endif %}
              {% endfor %}

              {# Append the last interval #}
              {% set ns.merged = ns.merged + [(ns.current_start, ns.current_end)] %}

              {% for start, end in ns.merged %}
              - {{ start.strftime('%H:%M') }} to {{ end.strftime('%H:%M') }}

              {% endfor %}
              {% else %}
              Dispatches not yet scheduled.
              {% endif %}
              {% endraw %}

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
              name: Hallway motion sensors
              entity: input_boolean.motion_sensors_enabled
            - type: tile
              name: Front door motion sensor
              entity: switch.front_door_motion_detection

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
            padding: '0'
            title-card:
              type: tile
              entity: {{ room.lights }}
              features_position: inline
              features:
                - type: light-brightness
            cards:
              {% for id in groups[room.lights].entities %}
              - type: tile
                entity: {{ id }}
                features_position: inline
                features:
                  - type: light-brightness
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

  {% endfor %}

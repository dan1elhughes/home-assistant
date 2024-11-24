views:
  - title: Home
    path: home
    icon: mdi:home
    type: sections
    sections:
      - type: grid
        column_span: 2
        cards:
          - type: horizontal-stack
            grid_options:
                columns: full
            cards:
            - type: entity
              entity: sensor.kingsclere_waste
              name: Waste
              show_name: true
              color: grey
            - type: entity
              entity: sensor.kingsclere_recycling
              name: Recycling
              show_name: true
              color: green
            - type: entity
              entity: sensor.kingsclere_garden
              name: Garden
              show_name: true
              color: brown
            - type: entity
              entity: sensor.kingsclere_glass
              name: Glass
              show_name: true
              color: light-green

          - type: horizontal-stack
            grid_options:
              columns: full
            cards:
            - type: weather-forecast
              show_current: true
              show_forecast: false
              entity: weather.home
              forecast_type: daily
              name: Kingsclere
            - type: vertical-stack
              cards:
                - type: tile
                  entity: climate.thermostat
                  features:
                    - type: target-temperature

          - type: custom:atomic-calendar-revive
            name: Calendar
            entities:
              - entity: calendar.k_d
                name: K&D
            maxDaysToShow: 5
            showDate: true
            grid_options:
              columns: full

      - type: grid
        cards:
          {% for room in rooms %}
          - type: heading
            badges:
              - type: entity
                entity: sensor.{{ room.id }}_sensor_temperature
              - type: entity
                entity: sensor.{{ room.id }}_sensor_humidity
            heading: {{ room.name }}
          {% if room.lights %}
          - type: custom:expander-card
            grid_options:
              columns: full
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

          {% if room.curtains %}
          - type: tile
            grid_options:
              columns: full
            entity: {{ room.curtains }}
          {% endif %}

        {% endfor %}

  - title: Energy
    path: energy
    icon: mdi:lightning-bolt
    type: sections
    sections:
      - type: grid
        cards:
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
          - type: heading
            heading: ID3
            heading_style: title
            icon: mdi:car
            badges:
              - type: entity
                entity: sensor.id3_battery_level
          - type: tile
            entity: sensor.id3_electric_range
            name: Range
            show_entity_picture: false
            vertical: false
            hide_state: false
          - type: tile
            entity: sensor.id3_charging_time_left
            name: Remaining charge time
            visibility:
              - condition: state
                entity: switch.id3_charging
                state: 'on'
          - type: map
            entities:
              - entity: device_tracker.id3_position
                name: ID3
            theme_mode: auto
      - type: grid
        cards:
          - type: heading
            heading: Zoe
            heading_style: title
            icon: mdi:car
            badges:
              - type: entity
                show_state: true
                show_icon: true
                entity: sensor.wp22lxc_battery
          - type: tile
            entity: sensor.wp22lxc_battery_autonomy
            name: Range
            icon: mdi:car-electric
          - type: tile
            entity: sensor.wp22lxc_charging_remaining_time
            name: Remaining charge time
            visibility:
              - condition: state
                entity: binary_sensor.wp22lxc_charging
                state: 'on'
          - type: map
            entities:
              - entity: device_tracker.wp22lxc_location
                name: Zoe
            theme_mode: auto

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

      - type: grid
        cards:
        - type: entities
          title: Quick controls
          state_color: true
          entities:
            - entity: switch.amplifier
              name: Amplifier
              secondary_info: none
            - entity: input_datetime.wake_up
              name: Wake up
              secondary_info: none
            - entity: input_datetime.lights_out
              name: Lights out
              secondary_info: none

      - type: grid
        cards:
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

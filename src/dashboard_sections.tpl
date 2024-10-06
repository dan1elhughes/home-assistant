views:
  - title: Home
    path: home
    icon: mdi:home
    type: sections
    sections:
      - type: grid
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
      {% for room in rooms %}
      - type: grid
        cards:
          - type: heading
            heading: {{ room.name }}
            tap_action:
              action: perform-action
              perform_action: input_select.select_option
              target:
                entity_id: input_select.active_room
              data:
                option: {{ room.id }}

            badges:
              - type: entity
                entity: sensor.{{ room.id }}_sensor_temperature

          - type: vertical-stack
            cards:

              {% if room.lights %}
              - type: tile
                entity: {{ room.lights }}
              {% endif %}

              {% if room.fan %}
              - type: tile
                entity: {{ room.fan }}
              {% endif %}

              {% if room.curtains %}
              - type: tile
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
          - graph: none
            type: sensor
            entity: sensor.octopus_energy_electricity_15p0706167_2000050773706_current_accumulative_consumption
            detail: 1
            name: Used today
          - graph: none
            type: sensor
            entity: sensor.accumulative_electricity_cost_without_standing_charge
            detail: 1
            name: Spent today
          - type: vertical-stack
            cards:
              - graph: line
                type: sensor
                entity: >-
                  sensor.octopus_energy_electricity_15p0706167_2000050773706_current_demand
                detail: 2
                name: Import
                icon: mdi:home-import-outline
      - type: grid
        cards:
          - type: heading
            heading: Gas
            heading_style: title
            icon: mdi:fire
          - graph: none
            type: sensor
            entity: sensor.octopus_energy_gas_g4p07003781500_7475340302_current_accumulative_consumption_kwh
            detail: 1
            name: Used today
          - graph: none
            type: sensor
            entity: sensor.accumulative_gas_cost_without_standing_charge
            detail: 1
            name: Spent today
          - type: vertical-stack
            cards:
              - graph: line
                type: sensor
                entity: sensor.octopus_energy_gas_g4p07003781500_7475340302_current_consumption
                detail: 2
                name: Import
                icon: mdi:home-import-outline

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

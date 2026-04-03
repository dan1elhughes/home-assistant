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
              {% for w in waste_collections %}
              - entity: {{ w.entity }}
                name: {{ w.name }}
              {% endfor %}

          - type: weather-forecast
            show_current: true
            show_forecast: false
            entity: weather.home
            forecast_type: hourly
            name: Kingsclere

          - type: tile
            entity: group.ceiling_lights
          - type: tile
            entity: group.room_lights

          - type: custom:calendar-card-pro
            entities:
              - calendar.k_d
            days_to_show: 5
            show_location: true

      - type: grid
        cards:
          {% for room in rooms|sort(attribute='id') %}
          - type: button
            name: {{ room.name | safe }}
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
              - type: entity
                entity: sensor.next_energy_intent
                show_icon: false
          - type: sensor
            name: Power
            entity: sensor.battery_total_power
            graph: line
            detail: 2
          - type: sensor
            name: Energy
            entity: sensor.envoy_122322027694_available_battery_energy
            graph: line
            detail: 2
          - type: markdown
            content: >
              {% raw %}
              {%- set events = state_attr('sensor.energy_intents', 'events') %}
              {%- set export_rates = state_attr('sensor.octopus_energy_electricity_15p0706167_2000060833200_export_current_day_rates', 'rates') %}
              {%- if events %}
                {# Create an empty list to hold our formatted lines #}
                {%- set ns = namespace(items=[]) %}

                {%- for event in events | sort(attribute='start') %}
                  {%- set start = as_datetime(event.start) %}
                  {%- set end = as_datetime(event.end) %}
                  {%- set start_local = as_local(start) %}
                  {%- set end_local = as_local(end) %}
                  {%- set event_date = start_local.date() %}
                  {%- set today = now().date() %}

                  {%- if event_date > today %}
                    {%- set day_label = ' (tomorrow)' %}
                  {%- elif event_date < today %}
                    {%- set day_label = ' (yesterday)' %}
                  {%- else %}
                    {%- set day_label = '' %}
                  {%- endif %}

                  {%- set max_rate = none %}
                  {%- if export_rates and event.intent | lower == 'discharge' %}
                    {%- for rate in export_rates %}
                      {%- set rate_start = as_datetime(rate.start) %}
                      {%- set rate_end = as_datetime(rate.end) %}
                      {%- if rate_start < end_local and rate_end > start_local %}
                        {%- if max_rate == none or rate.value_inc_vat > max_rate %}
                          {%- set max_rate = rate.value_inc_vat %}
                        {%- endif %}
                      {%- endif %}
                    {%- endfor %}
                  {%- endif %}

                  {# Build the string for this specific event #}
                  {%- set rate_display = ' @ ' ~ '%.1f'|format(max_rate * 100) ~ 'p' if max_rate else '' %}
                  {%- set line = '- ' ~ start_local.strftime('%H:%M') ~ ' - ' ~ end_local.strftime('%H:%M') ~ ': **' ~ event.intent ~ '**' ~ day_label ~ rate_display %}

                  {# Append it to our namespace list #}
                  {%- set ns.items = ns.items + [line] %}
                {%- endfor %}

                {# Print the final list all at once, separated by newlines #}
                {{- ns.items | join('\n') }}

              {%- else %}
                No scheduled intents
              {%- endif %}
              {% endraw %}

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
              - type: entity
                entity: sensor.central_heating_hvac_action
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
            heading: Battery management
            heading_style: title
            icon: mdi:battery
          - type: history-graph
            hours_to_show: 10
            entities:
              - entity: sensor.power_requirement_until_cheap_slot
                name: Energy needed
              - entity: sensor.envoy_122322027694_available_battery_energy
                name: Energy available
            max_y_axis: 15000
            min_y_axis: 0
          - type: vertical-stack
            cards:
              - type: tile
                name: Exportable battery
                entity: sensor.exportable_battery
                icon: mdi:battery-arrow-up-outline
              - type: tile
                name: Reserved battery
                entity: sensor.power_requirement_until_cheap_slot
                icon: mdi:battery-arrow-down-outline
              - type: tile
                name: Idle power draw
                entity: input_number.idle_power_draw
                icon: mdi:power-plug-outline
                features:
                  - style: buttons
                    type: numeric-input
                features_position: inline
              - type: tile
                name: Battery lower discharge limit
                entity: input_number.battery_lower_discharge_limit
                icon: mdi:home-battery-outline
                features:
                  - style: buttons
                    type: numeric-input
                features_position: inline

      - type: grid
        visibility:
          - condition: or
            conditions:
              - condition: state
                entity: switch.octopus_energy_00000000_0002_4000_8020_00000008191c_intelligent_smart_charge
                state: "on"
              - condition: state
                entity: input_boolean.smart_charge_tonight
                state: "on"
        cards:
          - type: heading
            heading: Smart charge
            heading_style: title
            icon: mdi:ev-station
          - type: tile
            entity: number.octopus_energy_00000000_0002_4000_8020_00000008191c_intelligent_charge_target
            name: Target
          - type: tile
            entity: select.octopus_energy_00000000_0002_4000_8020_00000008191c_intelligent_target_time
            name: Time
          - type: markdown
            content: >+
              {% raw %}
              {% set dispatches = state_attr('binary_sensor.octopus_energy_00000000_0002_4000_8020_00000008191c_intelligent_dispatching', 'planned_dispatches') %}
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
              entity: light.front_lights
              name: Front lights
            - type: tile
              name: Hallway motion sensors
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
              - type: entity
                entity: input_number.barn_ac_default_temp
                name: Barn AC default
                secondary_info: none
              - type: entity
                entity: input_number.office_ac_default_temp
                name: Office AC default
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

  {% for room in rooms|sort(attribute='id') %}
  - title: {{ room.name | safe }}
    path: sub-{{ room.id }}
    subview: true
    badges:
      {% for id in room.badges %}
      - type: entity
        entity: {{ id }}
      {% endfor %}
      {% if room.co2_sensor %}
      - type: entity
        entity: sensor.{{ room.co2_sensor }}_co2
      {% endif %}
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
            heading: {{ room.name | safe }}

          {% if room.lights %}
          - type: tile
            entity: {{ room.lights }}
            features_position: inline
            features:
              - type: light-brightness
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

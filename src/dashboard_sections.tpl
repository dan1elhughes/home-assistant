{% import './macros/lights.tpl' as lights with context %}

views:
  - title: Home
    path: home
    icon: mdi:home
    type: sections
    badges:
      - type: entity
        entity: sensor.envoy_122322027694_battery
      - type: entity
        entity: sensor.predbat_intent
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
        visibility:
          - condition: or
            conditions:
              - condition: state
                entity: binary_sensor.octopus_energy_a_fad3b08a_octoplus_saving_sessions
                state: "on"
              - condition: state
                entity: binary_sensor.octopus_energy_a_fad3b08a_octoplus_free_electricity_session
                state: "on"
        cards:
          - type: heading
            heading: Octopus events
            heading_style: title
            icon: mdi:gift
          - type: entity
            entity: binary_sensor.octopus_energy_a_fad3b08a_octoplus_saving_sessions
            name: Saving session
          - type: entity
            entity: binary_sensor.octopus_energy_a_fad3b08a_octoplus_free_electricity_session
            name: Free electricity

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

  - type: sidebar
    title: Predbat
    path: predbat
    icon: mdi:chart-bell-curve
    cards:
      - type: custom:html-template-card
        ignore_line_breaks: true
        content: |
          {% raw %}
          {{ state_attr('predbat.plan_html', 'html') }}
          {% endraw %}
        view_layout:
          position: main

      - type: entities
        show_header_toggle: false
        entities:
          - type: section
            label: State
          - entity: switch.predbat_active
            name: Active
            icon: mdi:robot-outline
            secondary_info: last-changed
          - entity: sensor.predbat_intent
            name: Intent
            icon: mdi:robot-outline
          - entity: select.predbat_mode
            name: Mode
            icon: mdi:cog
          - type: section
            label: Overrides
          - entity: select.predbat_manual_charge
            name: Force charge
            icon: mdi:battery-arrow-up
          - entity: select.predbat_manual_export
            name: Force export
            icon: mdi:battery-arrow-down
          - entity: select.predbat_manual_demand
            name: Force demand
            icon: mdi:home-battery
          - type: section
            label: Combine slots
          - entity: switch.predbat_combine_charge_slots
            name: Combine charge
            icon: mdi:vector-combine
          - entity: switch.predbat_combine_export_slots
            name: Combine export
            icon: mdi:vector-combine
          - type: section
            label: Cost
          - entity: input_number.predbat_metric_battery_cycle
            name: Cycle cost
            icon: mdi:currency-gbp
          - entity: input_number.predbat_carbon_metric
            name: Carbon metric
            icon: mdi:molecule-co2
          - entity: input_number.predbat_holiday_days_left
            name: Holiday days
            icon: mdi:beach
        view_layout:
          position: sidebar

      - type: markdown
        title: Enphase schedule
        content: |
          {% raw %}
          {%- set schedules = state_attr('sensor.enphase_schedules_summary', 'schedules') %}
          {%- set weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] %}
          {%- if schedules %}
          {%- set ns = namespace(items=[]) %}
            {%- for schedule in schedules | sort(attribute='start') | sort(attribute='days') %}
              {%- set day_ns = namespace(items=[]) %}
              {%- for day in schedule.days | default([]) %}
                {%- set day_ns.items = day_ns.items + [weekdays[day - 1] if day >= 1 and day <= 7 else day] %}
              {%- endfor %}

              {%- if day_ns.items | length == 7 %}
                {%- set days_label = ' (Every day)' %}
              {%- elif day_ns.items %}
                {%- set days_label = ' (' ~ day_ns.items | join(', ') ~ ')' %}
              {%- else %}
                {%- set days_label = '' %}
              {%- endif %}

              {%- if schedule.type | lower == 'cfg' %}
                {%- set action = '⚡ Charge' %}
              {%- elif schedule.type | lower == 'dtg' %}
                {%- set action = '🔋 Export' %}
              {%- else %}
                {%- set action = schedule.type | upper %}
              {%- endif %}

              {%- set line = '- ' ~ schedule.start ~ ' – ' ~ schedule.end ~ ': **' ~ action ~ '** ' ~ schedule.limit ~ '%' ~ days_label %}
            {%- set ns.items = ns.items + [line] %}
          {%- endfor %}
          {{ ns.items | join('\n') }}
          {%- else %}
          No battery schedule
          {%- endif %}
          {% endraw %}
        view_layout:
          position: sidebar

      - type: markdown
        title: Octopus schedule
        content: |
          {% raw %}
          {%- set cars = [
              ('ID3', 'binary_sensor.octopus_energy_00000000_0002_4000_8020_00000008191c_intelligent_dispatching'),
              ('Zoe', 'binary_sensor.octopus_energy_00000000_0002_4000_8020_00000011612f_intelligent_dispatching')
            ] %}
          {%- set weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] %}
          {%- set ns = namespace(items=[]) %}
          {%- for name, entity in cars %}
            {%- set planned = state_attr(entity, 'planned_dispatches') | default([]) %}
            {%- for d in planned | sort(attribute='start') %}
              {%- set s = d.start | as_datetime %}
              {%- set e = d.end | as_datetime %}
              {%- if e > now() %}
                {%- set kwh = (d.charge_in_kwh | float(0) | abs) | round(1) %}
                {%- set active = now() >= s and now() < e %}
                {%- set icon = '⚡' if active else '🕐' %}
                {%- set status = 'Charging' if active else 'Scheduled' %}
                {%- if s.date() == e.date() %}
                  {%- set end_str = e.strftime('%H:%M') %}
                {%- else %}
                  {%- set end_str = e.strftime('%H:%M') ~ ' (' ~ weekdays[e.weekday()] ~ ')' %}
                {%- endif %}
                {%- set line = '- ' ~ name ~ ' · ' ~ s.strftime('%H:%M') ~ ' – ' ~ end_str ~ ': **' ~ icon ~ ' ' ~ status ~ '** ' ~ kwh ~ ' kWh' %}
                {%- set ns.items = ns.items + [line] %}
              {%- endif %}
            {%- endfor %}
          {%- endfor %}
          {{ ns.items | join('\n') if ns.items else 'No scheduled dispatch' }}
          {% endraw %}
        view_layout:
          position: sidebar
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

  - type: sections
    title: Maintenance
    path: maintenance
    icon: mdi:clipboard-list
    sections:
      - type: grid
        cards:
          - type: custom:battery-state-card
            title: Device Batteries
            filter:
              include:
                - name: "attributes.device_class"
                  value: "battery"
              exclude:
                - name: "entity_id"
                  value: "binary_sensor.*"
                - name: "entity_id"
                  value: "sensor.envoy_122322027694_reserve_battery_level"
                - name: "entity_id"
                  value: "sensor.predbat_enphase_0_reserve"
            sort:
              - state
            collapse: 8
            secondary_info: "{last_changed}"
            colors:
              steps:
                - value: 20
                  color: "#e74c3c"
                - value: 50
                  color: "#f39c12"
                - value: 100
                  color: "#27ae60"

      - type: grid
        cards:
          - type: heading
            heading: Appliances
            heading_style: title
            icon: mdi:washing-machine
          - type: tile
            entity: sensor.dishwasher_rinse_aid_nearly_empty
            name: Rinse aid
            icon: mdi:sparkles
          - type: tile
            entity: sensor.dishwasher_salt_nearly_empty
            name: Salt
            icon: mdi:shaker-outline
          - type: tile
            entity: sensor.washer_dryer_poor_i_dos_1_fill_level
            name: Laundry liquid
            icon: mdi:soap
          - type: tile
            entity: sensor.washer_dryer_poor_i_dos_2_fill_level
            name: Softener
            icon: mdi:soap
          - type: tile
            entity: sensor.upstairs_error
            name: Upstairs error
          - type: tile
            entity: sensor.downstairs_error
            name: Downstairs error

  - type: sections
    max_columns: 4
    title: Smart charge
    path: smart-charge
    icon: mdi:car-electric
    sections:
      - type: grid
        cards:
          - type: heading
            heading: Zappi
            heading_style: title
            icon: mdi:ev-plug-type2
          - type: tile
            entity: select.myenergi_zappi_charge_mode
            name: Charge mode
            hide_state: true
            features_position: inline
            features:
              - type: select-options
            grid_options:
              columns: full
          - type: tile
            entity: sensor.myenergi_zappi_plug_status
            name: Plug status
          - type: tile
            entity: sensor.myenergi_zappi_charge_added_session
            name: Session charge

      - type: grid
        cards:
          - type: heading
            heading: ID3
            heading_style: title
            icon: mdi:car-electric
          - type: tile
            entity: switch.octopus_energy_00000000_0002_4000_8020_00000008191c_intelligent_smart_charge
            name: Smart charge
            features_position: inline
            features:
              - type: toggle
          - type: tile
            entity: number.octopus_energy_00000000_0002_4000_8020_00000008191c_intelligent_charge_target
            name: Charge target
            features_position: inline
            features:
              - type: numeric-input
                style: slider
            grid_options:
              columns: full
          - type: tile
            entity: select.octopus_energy_00000000_0002_4000_8020_00000008191c_intelligent_target_time
            name: Target time
            hide_state: true
            features_position: inline
            features:
              - type: select-options
            grid_options:
              columns: full

      - type: grid
        cards:
          - type: heading
            heading: Zoe
            heading_style: title
            icon: mdi:car-electric
          - type: tile
            entity: switch.octopus_energy_00000000_0002_4000_8020_00000011612f_intelligent_smart_charge
            name: Smart charge
            features_position: inline
            features:
              - type: toggle
          - type: tile
            entity: number.octopus_energy_00000000_0002_4000_8020_00000011612f_intelligent_charge_target
            name: Charge target
            features_position: inline
            features:
              - type: numeric-input
                style: slider
            grid_options:
              columns: full
          - type: tile
            entity: select.octopus_energy_00000000_0002_4000_8020_00000011612f_intelligent_target_time
            name: Target time
            hide_state: true
            features_position: inline
            features:
              - type: select-options
            grid_options:
              columns: full

      - type: grid
        cards:
          - type: heading
            heading: Schedule
            heading_style: title
            icon: mdi:clock-outline
          - type: tile
            entity: input_boolean.auto_enable_smart_charge
            name: Auto enable
            features_position: inline
            features:
              - type: toggle
          - type: tile
            entity: input_datetime.smart_charge_start
            name: Start
            features_position: inline
            features:
              - type: date-set
            grid_options:
              columns: full
          - type: tile
            entity: input_boolean.auto_disable_smart_charge
            name: Auto disable
            features_position: inline
            features:
              - type: toggle
          - type: tile
            entity: input_datetime.smart_charge_end
            name: End
            features_position: inline
            features:
              - type: date-set
            grid_options:
              columns: full

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

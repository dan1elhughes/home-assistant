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

      - type: tile
        entity: input_select.active_room
        features:
          - type: select-options

      {% for room in rooms %}
      {% if room.lights %}
      - type: tile
        entity: {{ room.lights }}
      {% endif %}
      {% endfor %}

      - type: tile
        entity: fan.fans

      - type: tile
        entity: group.presence_home
        icon: mdi:home-account

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
      - type: tile
        entity: climate.{{room.id}}
        icon_tap_action:
          action: toggle
        features:
          - style: icons
            type: climate-preset-modes
            preset_modes:
              - away
              - comfort
              - home
              - sleep
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
          entity: sensor.energy_cost_per_hour
          name: Cost per hour
          icon: mdi:currency-gbp
        - type: horizontal-stack
          cards:
            - type: sensor
              graph: line
              entity: sensor.octopus_energy_electricity_20j0046498_2000052144657_current_demand
              detail: 2
              name: Demand
            - type: sensor
              graph: line
              entity: sensor.octopus_energy_electricity_20j0046498_2000052144657_current_rate
              detail: 2
              name: Rate
        - type: horizontal-stack
          cards:
            - graph: none
              type: sensor
              name: Used today
              entity: sensor.octopus_energy_electricity_20j0046498_2000052144657_current_accumulative_consumption
              detail: 1
            - graph: none
              type: sensor
              entity: sensor.octopus_energy_electricity_20j0046498_2000052144657_current_accumulative_cost
              detail: 1
              name: Spent today
        - type: horizontal-stack
          cards:
            - graph: none
              type: sensor
              name: Used yesterday
              entity: sensor.octopus_energy_electricity_20j0046498_2000052144657_previous_accumulative_consumption
              detail: 1
            - graph: none
              type: sensor
              entity: sensor.octopus_energy_electricity_20j0046498_2000052144657_previous_accumulative_cost
              detail: 1
              name: Spent yesterday

        - type: custom:expander-card
          title: Targets
          cards:
            - type: entities
              entities:
                {% for target in agile_targets %}
                - type: section
                  label: "{{ target.name }}"
                {% for group in target.groups %}
                - entity: "{{ group }}"
                  name: "{{ group }}"
                {% endfor %}
                - type: attribute
                  name: "Next time"
                  entity: "{{ target.id }}"
                  attribute: next_time
                - type: attribute
                  name: "Average cost"
                  icon: mdi:currency-gbp
                  entity: "{{ target.id }}"
                  attribute: overall_average_cost
                {% endfor %}

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

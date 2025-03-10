<template>
  <v-card class="controls-card">
    <v-card-title class="controls-title">显示选项</v-card-title>
    <v-card-text class="py-1">
      <v-row>
        <v-col cols="12" sm="4">
          <v-switch
            v-model="localShowTrails"
            label="显示轨迹"
            color="primary"
            hide-details
            class="control-switch"
            dense
          ></v-switch>
        </v-col>
        <v-col cols="12" sm="4">
          <v-switch
            v-model="localShowVisionRange"
            label="显示视野范围"
            color="primary"
            hide-details
            class="control-switch"
            dense
          ></v-switch>
        </v-col>
        <v-col cols="12" sm="4">
          <v-switch
            v-model="localShowCommunicationRange"
            label="显示通信范围"
            color="primary"
            hide-details
            class="control-switch"
            dense
          ></v-switch>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script>
export default {
  name: 'SimulationControls',
  props: {
    showTrails: {
      type: Boolean,
      default: true
    },
    showVisionRange: {
      type: Boolean,
      default: false
    },
    showCommunicationRange: {
      type: Boolean,
      default: false
    }
  },
  computed: {
    localShowTrails: {
      get() {
        return this.showTrails;
      },
      set(value) {
        this.$emit('update:showTrails', value);
      }
    },
    localShowVisionRange: {
      get() {
        return this.showVisionRange;
      },
      set(value) {
        this.$emit('update:showVisionRange', value);
      }
    },
    localShowCommunicationRange: {
      get() {
        return this.showCommunicationRange;
      },
      set(value) {
        this.$emit('update:showCommunicationRange', value);
      }
    }
  }
}
</script>

<style scoped>
.controls-card {
  border-radius: 4px;
  margin-top: 8px;
  margin-bottom: 8px;
}

.controls-title {
  font-size: 0.9rem;
  padding: 4px 12px !important;
  min-height: 32px !important;
}

.control-switch {
  margin: 0 !important;
  height: 28px !important;
}

.v-switch.control-switch >>> .v-label {
  font-size: 0.75rem !important;
}

.v-row, .v-col {
  padding: 2px !important;
  margin: 0 !important;
}

@media (max-height: 768px) {
  .controls-title {
    padding: 2px 12px !important;
    min-height: 28px !important;
  }
  
  .control-switch {
    height: 24px !important;
  }
}
</style>
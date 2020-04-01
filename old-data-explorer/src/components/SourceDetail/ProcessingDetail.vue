<template>
  <b-card title="Processing Details">
    <b-card-text>
      <dl class="row">
        <dt class="col-sm-5">
          Notes:
        </dt>
        <dd class="col-sm-7">
          {{ sourceRunDetail.notes }}
        </dd>
        <dt class="col-sm-5">
          Stamp Size:
        </dt>
        <dd class="col-sm-7">
          {{ piaaRecord.stamp_size }}
        </dd>
        <dt class="col-sm-5">
          Num refs:
        </dt>
        <dd class="col-sm-7">
          {{ sourceRunDetail.num_refs }}
        </dd>
        <dt class="col-sm-5">
          Sequence ID:
        </dt>
        <dd class="col-sm-7">
          <a
            :href="'/observations/' + sourceRunDetail.sequence_id"
            target="_blank"
          >{{ sourceRunDetail.sequence_id }}</a>
        </dd>
        <dt class="col-sm-5">
          Run ID:
        </dt>
        <dd class="col-sm-7">
          {{ sourceRunDetail.piaa_document_id }}
        </dd>
      </dl>
    </b-card-text>
  </b-card>
</template>

<script>
import { mapState } from 'vuex'

export default {
  name: 'ProcessingDetail',
  computed: {
    ...mapState(['sourceRunDetail', 'piaaRecord'])
  },
  data() {
    return {}
  }
}
</script>

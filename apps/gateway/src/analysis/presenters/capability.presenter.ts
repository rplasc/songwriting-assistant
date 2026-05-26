import { Injectable } from '@nestjs/common';
import {
  CAPABILITY_KEYS,
  CapabilityKey,
  CapabilityReasonCode,
  CapabilityStatus,
} from '../../common/enums/capability.enum';
import {
  DraftAnalysisCapabilities,
  UpstreamCapability,
} from '../../fastapi/dto/fastapi-responses';

export interface CapabilityPayload {
  status: CapabilityStatus;
  reason_code: CapabilityReasonCode | null;
}

export type CapabilitiesPayload = Record<CapabilityKey, CapabilityPayload>;

@Injectable()
export class CapabilityPresenter {
  toClient(input: DraftAnalysisCapabilities): CapabilitiesPayload {
    const out = {} as CapabilitiesPayload;
    for (const key of CAPABILITY_KEYS) {
      out[key] = this.normalize(input[key]);
    }
    return out;
  }

  /**
   * Aggregate readiness: true if any capability is not 'unsupported'. Used
   * by the draft-analysis presenter to derive the top-level analysis_status.
   */
  anyEnabled(input: DraftAnalysisCapabilities): boolean {
    return CAPABILITY_KEYS.some(
      (k) => input[k]?.status && input[k].status !== 'unsupported',
    );
  }

  private normalize(cap: UpstreamCapability | undefined): CapabilityPayload {
    if (!cap) {
      return { status: 'unsupported', reason_code: 'language_unsupported' };
    }
    return {
      status: cap.status,
      reason_code: cap.reason_code ?? null,
    };
  }
}

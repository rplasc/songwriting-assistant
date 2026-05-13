import { Injectable } from '@nestjs/common';
import { FastapiClient } from '../fastapi/fastapi.client';

@Injectable()
export class DependencyHealthService {
  constructor(private readonly fastapi: FastapiClient) {}

  async checkFastapi(): Promise<{ reachable: boolean }> {
    return { reachable: await this.fastapi.ping() };
  }
}

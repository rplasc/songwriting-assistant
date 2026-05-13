import { Controller, Get } from '@nestjs/common';
import { DependencyHealthService } from './dependency-health.service';

@Controller('health')
export class HealthController {
  constructor(private readonly deps: DependencyHealthService) {}

  @Get()
  getHealth() {
    return { status: 'ok', service: 'nestjs-api' };
  }

  @Get('dependencies')
  async getDependencies() {
    const fastapi = await this.deps.checkFastapi();
    return {
      status: fastapi.reachable ? 'ok' : 'degraded',
      fastapi,
    };
  }
}

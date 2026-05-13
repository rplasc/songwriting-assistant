import { Module } from '@nestjs/common';
import { FastapiModule } from '../fastapi/fastapi.module';
import { DependencyHealthService } from './dependency-health.service';
import { HealthController } from './health.controller';

@Module({
  imports: [FastapiModule],
  controllers: [HealthController],
  providers: [DependencyHealthService],
})
export class HealthModule {}

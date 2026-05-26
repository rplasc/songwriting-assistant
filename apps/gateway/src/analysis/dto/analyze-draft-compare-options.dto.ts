import { IsBoolean, IsOptional } from 'class-validator';

export class AnalyzeDraftCompareOptionsDto {
  @IsOptional()
  @IsBoolean()
  compareMotifs?: boolean;

  @IsOptional()
  @IsBoolean()
  compareRepetition?: boolean;

  @IsOptional()
  @IsBoolean()
  compareSections?: boolean;

  @IsOptional()
  @IsBoolean()
  compareConsistency?: boolean;
}

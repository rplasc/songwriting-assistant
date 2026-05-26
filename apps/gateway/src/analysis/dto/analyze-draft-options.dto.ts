import { IsBoolean, IsOptional } from 'class-validator';

export class AnalyzeDraftOptionsDto {
  @IsOptional()
  @IsBoolean()
  includeSemanticRepetition?: boolean;

  @IsOptional()
  @IsBoolean()
  includeMotifTracking?: boolean;

  @IsOptional()
  @IsBoolean()
  includeSectionContrast?: boolean;

  @IsOptional()
  @IsBoolean()
  includeConsistencyHints?: boolean;
}

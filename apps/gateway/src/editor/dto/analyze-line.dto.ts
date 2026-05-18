import { Transform } from 'class-transformer';
import {
  IsIn,
  IsNotEmpty,
  IsOptional,
  IsString,
  MaxLength,
} from 'class-validator';

export type RhymeMode = 'perfect' | 'near';

export class AnalyzeLineDto {
  @IsString()
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @IsNotEmpty()
  @MaxLength(500)
  line!: string;

  @IsOptional()
  @IsIn(['perfect', 'near'])
  rhyme_mode?: RhymeMode;
}

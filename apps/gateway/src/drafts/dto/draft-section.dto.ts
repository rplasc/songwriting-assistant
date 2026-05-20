import { Transform } from 'class-transformer';
import {
  IsInt,
  IsNotEmpty,
  IsString,
  MaxLength,
  Min,
} from 'class-validator';

export class DraftSectionInputDto {
  @IsString()
  @Transform(({ value }) => (typeof value === 'string' ? value.trim() : value))
  @IsNotEmpty()
  @MaxLength(40)
  label!: string;

  @IsInt()
  @Min(1)
  lineStart!: number;

  @IsInt()
  @Min(1)
  lineEnd!: number;
}

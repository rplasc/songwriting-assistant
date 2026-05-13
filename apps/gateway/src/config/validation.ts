import * as Joi from 'joi';

export const envValidationSchema = Joi.object({
  NODE_ENV: Joi.string()
    .valid('development', 'production', 'test')
    .default('development'),
  PORT: Joi.number().integer().min(1).max(65535).default(3000),
  FASTAPI_BASE_URL: Joi.string().uri().required(),
  FASTAPI_TIMEOUT_MS: Joi.number().integer().min(100).default(5000),
  CORS_ORIGIN: Joi.string().default('*'),
});

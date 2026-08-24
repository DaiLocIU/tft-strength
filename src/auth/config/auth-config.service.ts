import { Injectable, Logger, OnModuleInit } from '@nestjs/common';

@Injectable()
export class AuthConfigService implements OnModuleInit {
  private readonly logger = new Logger(AuthConfigService.name);

  onModuleInit() {
    this.validate();
  }

  private validate(): void {
    const isProduction = process.env.NODE_ENV === 'production';

    if (isProduction) {
      const requiredEnvVars = [
        'JWT_SECRET',
        'JWT_REFRESH_SECRET',
        'GOOGLE_CLIENT_ID',
        'GOOGLE_CLIENT_SECRET',
      ];

      const missing = requiredEnvVars.filter((key) => !process.env[key]);
      if (missing.length > 0) {
        throw new Error(
          `[AuthConfigService] Fatal: Missing required environment variables in production: ${missing.join(', ')}`,
        );
      }
    } else {
      if (!process.env.JWT_SECRET) {
        this.logger.warn(
          'JWT_SECRET is not set. Using default development secret key.',
        );
      }
      if (!process.env.JWT_REFRESH_SECRET) {
        this.logger.warn(
          'JWT_REFRESH_SECRET is not set. Using default development refresh secret key.',
        );
      }
    }
  }

  get jwtSecret(): string {
    return process.env.JWT_SECRET || 'defaultJwtSecretKey';
  }

  get jwtExpiresIn():
    `${number}m` | `${number}s` | `${number}h` | `${number}d` {
    return (
      (process.env.JWT_EXPIRES_IN as
        `${number}m` | `${number}s` | `${number}h` | `${number}d`) || '5m'
    );
  }

  get jwtRefreshSecret(): string {
    return process.env.JWT_REFRESH_SECRET || 'defaultRefreshSecretKey';
  }

  get jwtRefreshExpiresIn():
    `${number}m` | `${number}s` | `${number}h` | `${number}d` {
    return (
      (process.env.JWT_REFRESH_EXPIRES_IN as
        `${number}m` | `${number}s` | `${number}h` | `${number}d`) || '7d'
    );
  }

  get googleClientId(): string {
    return process.env.GOOGLE_CLIENT_ID || '';
  }

  get googleClientSecret(): string {
    return process.env.GOOGLE_CLIENT_SECRET || '';
  }

  get googleCallbackUrl(): string {
    return (
      process.env.GOOGLE_CALLBACK_URL ||
      'http://localhost:3000/auth/google/callback'
    );
  }

  get frontendUrl(): string {
    return process.env.FRONTEND_URL || 'http://localhost:5173';
  }
}

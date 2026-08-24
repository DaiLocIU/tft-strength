import { Module } from '@nestjs/common';
import { JwtModule } from '@nestjs/jwt';
import { PassportModule } from '@nestjs/passport';
import { PrismaModule } from '../prisma/prisma.module';
import { AuthController } from './auth.controller';
import { AuthService } from './auth.service';
import { AuthConfigService } from './config/auth-config.service';
import { JwtAuthGuard } from './guards/jwt-auth.guard';
import { JwtRefreshAuthGuard } from './guards/jwt-refresh-auth.guard';
import { PrismaUserStore } from './stores/prisma-user.store';
import { USER_STORE } from './stores/user.store.interface';
import { GoogleStrategy } from './strategies/google.strategy';
import { JwtStrategy } from './strategies/jwt.strategy';
import { RefreshTokenStrategy } from './strategies/refresh-token.strategy';

@Module({
  imports: [
    PrismaModule,
    PassportModule,
    JwtModule.registerAsync({
      inject: [AuthConfigService],
      useFactory: (authConfig: AuthConfigService) => ({
        secret: authConfig.jwtSecret,
        signOptions: {
          expiresIn: authConfig.jwtExpiresIn,
        },
      }),
    }),
  ],
  controllers: [AuthController],
  providers: [
    AuthConfigService,
    AuthService,
    GoogleStrategy,
    JwtStrategy,
    RefreshTokenStrategy,
    JwtAuthGuard,
    JwtRefreshAuthGuard,
    {
      provide: USER_STORE,
      useClass: PrismaUserStore,
    },
  ],
  exports: [
    AuthService,
    AuthConfigService,
    USER_STORE,
    JwtAuthGuard,
    JwtRefreshAuthGuard,
  ],
})
export class AuthModule {}

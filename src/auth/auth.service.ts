import { ForbiddenException, Inject, Injectable, Logger } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcrypt';
import { UserModel } from '../../generated/prisma/models/User';
import { AuthConfigService } from './config/auth-config.service';
import { USER_STORE, type UserStore } from './stores/user.store.interface';

export interface GoogleUserPayload {
  googleId: string;
  email: string;
  name?: string;
  avatar?: string;
}

export interface TokensResponse {
  accessToken: string;
  refreshToken: string;
}

@Injectable()
export class AuthService {
  private readonly logger = new Logger(AuthService.name);

  constructor(
    @Inject(USER_STORE)
    private readonly userStore: UserStore,
    private readonly jwtService: JwtService,
    private readonly authConfig: AuthConfigService,
  ) {}

  async generateTokens(userId: number, email: string): Promise<TokensResponse> {
    const payload = { sub: userId, email };

    const [accessToken, refreshToken] = await Promise.all([
      this.jwtService.signAsync(payload, {
        secret: this.authConfig.jwtSecret,
        expiresIn: this.authConfig.jwtExpiresIn,
      }),
      this.jwtService.signAsync(payload, {
        secret: this.authConfig.jwtRefreshSecret,
        expiresIn: this.authConfig.jwtRefreshExpiresIn,
      }),
    ]);

    await this.updateHashedRefreshToken(userId, refreshToken);

    return { accessToken, refreshToken };
  }

  async updateHashedRefreshToken(
    userId: number,
    refreshToken: string,
  ): Promise<void> {
    const salt = await bcrypt.genSalt(10);
    const hash = await bcrypt.hash(refreshToken, salt);

    this.logger.debug(`Stored hashed refresh token for user #${userId}`);

    await this.userStore.update({
      where: { id: userId },
      data: { hashedRefreshToken: hash },
    });
  }

  async validateGoogleUser(
    payload: GoogleUserPayload,
  ): Promise<{ user: UserModel; accessToken: string; refreshToken: string }> {
    this.logger.log(
      `Validating Google user profile for email: ${payload.email}`,
    );

    let user = await this.userStore.findUnique({
      where: { email: payload.email },
    });

    if (!user) {
      this.logger.log(`Creating new user account for ${payload.email}`);
      user = await this.userStore.create({
        data: {
          email: payload.email,
          name: payload.name,
          avatar: payload.avatar,
          googleId: payload.googleId,
        },
      });
    } else if (!user.googleId) {
      this.logger.log(`Linking Google account to existing user #${user.id}`);
      user = await this.userStore.update({
        where: { id: user.id },
        data: {
          googleId: payload.googleId,
          avatar: payload.avatar ?? user.avatar,
        },
      });
    } else {
      this.logger.debug(`Existing user #${user.id} authenticated.`);
    }

    const tokens = await this.generateTokens(user.id, user.email);

    return {
      user,
      accessToken: tokens.accessToken,
      refreshToken: tokens.refreshToken,
    };
  }

  async refreshTokens(
    userId: number,
    refreshToken: string,
  ): Promise<TokensResponse> {
    const user = await this.userStore.findUnique({
      where: { id: userId },
    });

    if (!user || !user.hashedRefreshToken) {
      throw new ForbiddenException('Access Denied');
    }

    const isMatch = await bcrypt.compare(refreshToken, user.hashedRefreshToken);

    if (!isMatch) {
      throw new ForbiddenException('Access Denied');
    }

    return this.generateTokens(user.id, user.email);
  }

  async logout(userId: number): Promise<{ message: string }> {
    await this.userStore.updateMany({
      where: { id: userId, hashedRefreshToken: { not: null } },
      data: { hashedRefreshToken: null },
    });

    return { message: 'Logged out successfully' };
  }
}

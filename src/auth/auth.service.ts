/* eslint-disable @typescript-eslint/no-unsafe-call */
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/no-unsafe-return */
/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/* eslint-disable @typescript-eslint/no-redundant-type-constituents */

// The rules above are disabled because PrismaClient (from generated/prisma/client.ts)
// uses // @ts-nocheck internally (Prisma v7 generated code), causing ESLint's
// type checker to evaluate Prisma types as `any`. These operations are safe at runtime.

import { ForbiddenException, Injectable } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcrypt';
import { UserModel } from '../../generated/prisma/models/User';
import { PrismaService } from '../prisma/prisma.service';

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
  constructor(
    private readonly prisma: PrismaService,
    private readonly jwtService: JwtService,
  ) {}

  async generateTokens(userId: number, email: string): Promise<TokensResponse> {
    const payload = { sub: userId, email };

    const [accessToken, refreshToken] = await Promise.all([
      this.jwtService.signAsync(payload, {
        secret: process.env.JWT_SECRET || 'defaultJwtSecretKey',
        expiresIn:
          (process.env.JWT_EXPIRES_IN as
            `${number}m` | `${number}s` | `${number}h` | `${number}d`) || '5m',
      }),
      this.jwtService.signAsync(payload, {
        secret: process.env.JWT_REFRESH_SECRET || 'defaultRefreshSecretKey',
        expiresIn:
          (process.env.JWT_REFRESH_EXPIRES_IN as
            `${number}m` | `${number}s` | `${number}h` | `${number}d`) || '7d',
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

    await this.prisma.user.update({
      where: { id: userId },
      data: { hashedRefreshToken: hash },
    });
  }

  async validateGoogleUser(
    payload: GoogleUserPayload,
  ): Promise<{ user: UserModel; accessToken: string; refreshToken: string }> {
    let user = await this.prisma.user.findUnique({
      where: { email: payload.email },
    });

    if (!user) {
      user = await this.prisma.user.create({
        data: {
          email: payload.email,
          name: payload.name,
          avatar: payload.avatar,
          googleId: payload.googleId,
        },
      });
    } else if (!user.googleId) {
      user = await this.prisma.user.update({
        where: { id: user.id },
        data: {
          googleId: payload.googleId,
          avatar: payload.avatar ?? user.avatar,
        },
      });
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
    const user = await this.prisma.user.findUnique({
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
    await this.prisma.user.updateMany({
      where: { id: userId, hashedRefreshToken: { not: null } },
      data: { hashedRefreshToken: null },
    });

    return { message: 'Logged out successfully' };
  }
}

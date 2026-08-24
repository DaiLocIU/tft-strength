import { Injectable, UnauthorizedException } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import type { Request } from 'express';
import { ExtractJwt, Strategy } from 'passport-jwt';
import { AuthConfigService } from '../config/auth-config.service';

export interface JwtRefreshPayload {
  sub: number;
  email: string;
}

@Injectable()
export class RefreshTokenStrategy extends PassportStrategy(
  Strategy,
  'jwt-refresh',
) {
  constructor(private readonly authConfigService: AuthConfigService) {
    super({
      jwtFromRequest: ExtractJwt.fromExtractors([
        ExtractJwt.fromAuthHeaderAsBearerToken(),
        (req: Request) => {
          return req?.body?.refreshToken as string;
        },
      ]),
      secretOrKey: authConfigService.jwtRefreshSecret,
      passReqToCallback: true,
    });
  }

  validate(req: Request, payload: JwtRefreshPayload) {
    const authHeader = req.get('Authorization');
    const bearerToken = authHeader?.replace('Bearer', '').trim();
    const refreshToken = bearerToken || (req.body?.refreshToken as string);

    if (!refreshToken) {
      throw new UnauthorizedException('Refresh token missing');
    }

    return {
      userId: payload.sub,
      email: payload.email,
      refreshToken,
    };
  }
}

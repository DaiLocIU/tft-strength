import { Injectable } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { Profile, Strategy, VerifyCallback } from 'passport-google-oauth20';
import { AuthConfigService } from '../config/auth-config.service';

@Injectable()
export class GoogleStrategy extends PassportStrategy(Strategy, 'google') {
  constructor(private readonly authConfigService: AuthConfigService) {
    super({
      clientID: authConfigService.googleClientId,
      clientSecret: authConfigService.googleClientSecret,
      callbackURL: authConfigService.googleCallbackUrl,
      scope: ['email', 'profile'],
    });
  }

  validate(
    accessToken: string,
    refreshToken: string,
    profile: Profile,
    done: VerifyCallback,
  ): void {
    const { id, name, emails, photos } = profile;

    const user = {
      googleId: id,
      email: emails?.[0]?.value ?? '',
      name:
        `${name?.givenName ?? ''} ${name?.familyName ?? ''}`.trim() ||
        undefined,
      avatar: photos?.[0]?.value,
    };

    done(null, user);
  }
}

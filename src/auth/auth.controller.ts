import {
  Controller,
  Get,
  HttpCode,
  HttpStatus,
  Post,
  Req,
  Res,
  UseGuards,
} from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';
import type { Request, Response } from 'express';
import { AuthService, GoogleUserPayload } from './auth.service';
import { AuthConfigService } from './config/auth-config.service';
import { JwtAuthGuard } from './guards/jwt-auth.guard';
import { JwtRefreshAuthGuard } from './guards/jwt-refresh-auth.guard';

@Controller('auth')
export class AuthController {
  constructor(
    private readonly authService: AuthService,
    private readonly authConfig: AuthConfigService,
  ) {}

  @Get('google')
  @UseGuards(AuthGuard('google'))
  googleAuth() {
    // Passport automatically redirects to Google Consent Screen
  }

  @Get('google/callback')
  @UseGuards(AuthGuard('google'))
  async googleAuthRedirect(@Req() req: Request, @Res() res: Response) {
    const googleUser = req.user as GoogleUserPayload;
    const authData = await this.authService.validateGoogleUser(googleUser);
    const frontendUrl = this.authConfig.frontendUrl;
    return res.redirect(
      `${frontendUrl}?accessToken=${authData.accessToken}&refreshToken=${authData.refreshToken}&user=${encodeURIComponent(JSON.stringify(authData.user))}`,
    );
  }

  @Post('google-dev')
  @HttpCode(HttpStatus.OK)
  async googleDevAuth(@Req() req: Request) {
    const body = (req.body as Partial<GoogleUserPayload>) || {};
    const googleUser: GoogleUserPayload = {
      googleId: body.googleId || '',
      email: body.email || '',
      name: body.name || '',
      avatar: body.avatar || '',
    };
    return this.authService.validateGoogleUser(googleUser);
  }

  @Post('refresh')
  @UseGuards(JwtRefreshAuthGuard)
  @HttpCode(HttpStatus.OK)
  async refreshTokens(@Req() req: Request) {
    const user = req.user as { userId: number; refreshToken: string };
    return this.authService.refreshTokens(user.userId, user.refreshToken);
  }

  @Post('logout')
  @UseGuards(JwtAuthGuard)
  @HttpCode(HttpStatus.OK)
  async logout(@Req() req: Request) {
    const user = req.user as { userId: number };
    return this.authService.logout(user.userId);
  }
}

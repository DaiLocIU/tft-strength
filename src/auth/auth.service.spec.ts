import { ForbiddenException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { Test, TestingModule } from '@nestjs/testing';
import * as bcrypt from 'bcrypt';
import { AuthService, GoogleUserPayload } from './auth.service';
import { AuthConfigService } from './config/auth-config.service';
import { MemoryUserStore } from './stores/memory-user.store';
import { USER_STORE } from './stores/user.store.interface';

describe('AuthService (with MemoryUserStore and AuthConfigService)', () => {
  let service: AuthService;
  let userStore: MemoryUserStore;
  let jwtService: JwtService;
  let authConfig: AuthConfigService;

  beforeEach(async () => {
    userStore = new MemoryUserStore();
    authConfig = new AuthConfigService();

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        AuthService,
        {
          provide: USER_STORE,
          useValue: userStore,
        },
        {
          provide: AuthConfigService,
          useValue: authConfig,
        },
        {
          provide: JwtService,
          useValue: {
            signAsync: jest.fn().mockImplementation((payload: any, options: any) => {
              const secret = options?.secret || 'testSecret';
              return Promise.resolve(`token_for_${payload.sub}_${secret}`);
            }),
          },
        },
      ],
    }).compile();

    service = module.get<AuthService>(AuthService);
    jwtService = module.get<JwtService>(JwtService);
  });

  afterEach(() => {
    userStore.reset();
  });

  describe('validateGoogleUser', () => {
    it('should create a new user when email does not exist in store', async () => {
      const payload: GoogleUserPayload = {
        googleId: 'google-123',
        email: 'newuser@example.com',
        name: 'New User',
        avatar: 'https://example.com/avatar.png',
      };

      const result = await service.validateGoogleUser(payload);

      expect(result.user).toBeDefined();
      expect(result.user.email).toBe('newuser@example.com');
      expect(result.user.googleId).toBe('google-123');
      expect(result.accessToken).toBeDefined();
      expect(result.refreshToken).toBeDefined();

      const inDb = await userStore.findUnique({ where: { email: 'newuser@example.com' } });
      expect(inDb).toBeDefined();
      expect(inDb?.hashedRefreshToken).toBeDefined();
    });

    it('should link Google ID to existing user account if email matches but googleId is null', async () => {
      const existing = await userStore.create({
        data: {
          email: 'existing@example.com',
          name: 'Existing Local User',
          avatar: null,
          googleId: null,
        },
      });

      const payload: GoogleUserPayload = {
        googleId: 'google-456',
        email: 'existing@example.com',
        name: 'Google Name',
        avatar: 'https://google.com/pic.jpg',
      };

      const result = await service.validateGoogleUser(payload);

      expect(result.user.id).toBe(existing.id);
      expect(result.user.googleId).toBe('google-456');

      const updated = await userStore.findUnique({ where: { id: existing.id } });
      expect(updated?.googleId).toBe('google-456');
      expect(updated?.avatar).toBe('https://google.com/pic.jpg');
    });

    it('should authenticate existing user who already has googleId', async () => {
      const existing = await userStore.create({
        data: {
          email: 'linked@example.com',
          name: 'Linked User',
          avatar: 'https://avatar.com/1.png',
          googleId: 'google-789',
        },
      });

      const payload: GoogleUserPayload = {
        googleId: 'google-789',
        email: 'linked@example.com',
      };

      const result = await service.validateGoogleUser(payload);

      expect(result.user.id).toBe(existing.id);
      expect(result.accessToken).toBeDefined();
    });
  });

  describe('refreshTokens', () => {
    it('should rotate tokens when a valid refresh token is presented', async () => {
      const rawRefreshToken = 'valid-refresh-token-xyz';
      const salt = await bcrypt.genSalt(10);
      const hash = await bcrypt.hash(rawRefreshToken, salt);

      const user = await userStore.create({
        data: {
          email: 'refresh@example.com',
          hashedRefreshToken: hash,
        },
      });

      const tokens = await service.refreshTokens(user.id, rawRefreshToken);

      expect(tokens.accessToken).toBeDefined();
      expect(tokens.refreshToken).toBeDefined();

      const updated = await userStore.findUnique({ where: { id: user.id } });
      expect(updated?.hashedRefreshToken).toBeDefined();
      // Should have rotated and rehashed new token
      expect(updated?.hashedRefreshToken).not.toBe(hash);
    });

    it('should throw ForbiddenException if user has no stored refresh token', async () => {
      const user = await userStore.create({
        data: {
          email: 'loggedout@example.com',
          hashedRefreshToken: null,
        },
      });

      await expect(
        service.refreshTokens(user.id, 'some-token'),
      ).rejects.toThrow(ForbiddenException);
    });

    it('should throw ForbiddenException if refresh token does not match stored hash', async () => {
      const salt = await bcrypt.genSalt(10);
      const hash = await bcrypt.hash('correct-token', salt);

      const user = await userStore.create({
        data: {
          email: 'tampered@example.com',
          hashedRefreshToken: hash,
        },
      });

      await expect(
        service.refreshTokens(user.id, 'wrong-token'),
      ).rejects.toThrow(ForbiddenException);
    });
  });

  describe('logout', () => {
    it('should revoke stored refresh token', async () => {
      const salt = await bcrypt.genSalt(10);
      const hash = await bcrypt.hash('token', salt);

      const user = await userStore.create({
        data: {
          email: 'active@example.com',
          hashedRefreshToken: hash,
        },
      });

      const response = await service.logout(user.id);
      expect(response.message).toBe('Logged out successfully');

      const updated = await userStore.findUnique({ where: { id: user.id } });
      expect(updated?.hashedRefreshToken).toBeNull();
    });
  });
});

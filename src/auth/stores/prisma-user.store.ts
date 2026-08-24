/* eslint-disable @typescript-eslint/no-unsafe-call */
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
/* eslint-disable @typescript-eslint/no-unsafe-return */
/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/* eslint-disable @typescript-eslint/no-redundant-type-constituents */

import { Injectable } from '@nestjs/common';
import { UserModel } from '../../../generated/prisma/models/User';
import { PrismaService } from '../../prisma/prisma.service';
import {
  UserCreateData,
  UserStore,
  UserUpdateData,
  UserUpdateManyWhereInput,
  UserWhereUniqueInput,
} from './user.store.interface';

@Injectable()
export class PrismaUserStore implements UserStore {
  constructor(private readonly prisma: PrismaService) {}

  async findUnique(args: {
    where: UserWhereUniqueInput;
  }): Promise<UserModel | null> {
    return await this.prisma.user.findUnique({
      where: args.where as any,
    });
  }

  async create(args: { data: UserCreateData }): Promise<UserModel> {
    return await this.prisma.user.create({
      data: args.data,
    });
  }

  async update(args: {
    where: { id: number };
    data: UserUpdateData;
  }): Promise<UserModel> {
    return await this.prisma.user.update({
      where: args.where,
      data: args.data,
    });
  }

  async updateMany(args: {
    where: UserUpdateManyWhereInput;
    data: UserUpdateData;
  }): Promise<{ count: number }> {
    return await this.prisma.user.updateMany({
      where: args.where as any,
      data: args.data,
    });
  }
}

import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { Tab3Page } from './tab3.page';
import { ChatService } from '../core/services/chat.service';
import { of } from 'rxjs';

describe('Tab3Page', () => {
  let component: Tab3Page;
  let fixture: ComponentFixture<Tab3Page>;
  let chatServiceMock: any;

  beforeEach(async () => {
    chatServiceMock = {
      getBreedInfo: jasmine.createSpy('getBreedInfo').and.returnValue(of({ found: true, breed: 'Test Breed' })),
      sendMessage: jasmine.createSpy('sendMessage').and.returnValue(Promise.resolve({ ok: true, body: { getReader: () => ({ read: () => Promise.resolve({ done: true }) }) } }))
    };

    await TestBed.configureTestingModule({
      imports: [Tab3Page, HttpClientTestingModule],
      providers: [
        { provide: ChatService, useValue: chatServiceMock }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(Tab3Page);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
